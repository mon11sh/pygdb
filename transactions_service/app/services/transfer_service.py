"""
Transfer Service

Handles transfer operations (FE012).

Business Logic:
1. Validate both from and to accounts via Account Service
2. Check both accounts are active
3. Verify PIN for source account
4. Validate amount
5. Check sufficient balance in source account
6. Check daily transfer limits (by privilege level)
7. Create transaction record
8. Debit source account, credit destination account
9. Log transaction to DB + file
"""

import logging
from typing import Dict, Any, Optional
from decimal import Decimal
from datetime import datetime

from app.exceptions.transaction_exceptions import (
    AccountNotFoundException,
    AccountNotActiveException,
    InvalidAmountException,
    InvalidPINException,
    TransferFailedException,
    ServiceUnavailableException,
    InsufficientFundsException,
    SameAccountTransferException,
    TransferLimitExceededException,
    DailyTransactionCountExceededException,
    PaymentProcessingError,
)
from app.config.settings import settings
from app.models.enums import TransactionType, TransferMode
from app.validation.validators import (
    AmountValidator,
    BalanceValidator,
    PINValidator,
    TransferValidator,
    TransferLimitValidator,
)
from app.integration.account_service_client import account_service_client
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.transfer_limit_repository import TransferLimitRepository
from app.repositories.transaction_log_repository import TransactionLogRepository
from app.repositories.idempotency_repository import IdempotencyRepository
from app.exceptions.idempotency_exception import IdempotencyException
# Import clients at top level but be careful of circular imports if any (should be fine here as they are in integration folder)
from app.integration.payment_gateway_client import payment_gateway_client
from app.integration.notification_client import notification_client

logger = logging.getLogger(__name__)


class TransferService:
    """Service for transfer operations."""

    def __init__(self,
                 transaction_repo: Optional[TransactionRepository] = None,
                 log_repo: Optional[TransactionLogRepository] = None,
                 limit_repo: Optional[TransferLimitRepository] = None):
        """Initialize service with repositories."""
        self.transaction_repo = transaction_repo or TransactionRepository()
        # limit_repo MUST come from the active provider (SQLAlchemy on mysql/sqlite,
        # asyncpg on postgres/supabase). The direct fallback only fits the asyncpg
        # path and would fail on mysql/sqlite where the asyncpg pool is not created.
        self.limit_repo = limit_repo or TransferLimitRepository()
        self.log_repo = log_repo or TransactionLogRepository()
        self.account_client = account_service_client
        # Clients are already imported
        self.payment_gateway_client = payment_gateway_client
        self.notification_client = notification_client

    async def process_transfer(
        self,
        from_account: int,
        to_account: int,
        amount: Decimal,
        pin: str,
        transfer_mode: TransferMode = TransferMode.NEFT,
        description: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process fund transfer operation.
        ...
        """
        i_own_key = False
        money_moved = False  # True only after BOTH legs settle; a failure after this must NOT release the key
        try:
            # STEP 0: Idempotency (insert-first). A completed key replays its
            # stored result; a duplicate still in progress is rejected (409)
            # rather than executing the transfer twice.
            if idempotency_key:
                completed = await IdempotencyRepository.get_completed_response(idempotency_key)
                if completed is not None:
                    logger.info(f"↩️ Idempotent replay for key {idempotency_key}; returning stored transfer result")
                    return completed
                if not await IdempotencyRepository.reserve(idempotency_key, "TRANSFER"):
                    completed = await IdempotencyRepository.get_completed_response(idempotency_key)
                    if completed is not None:
                        return completed
                    raise IdempotencyException("A transfer with this Idempotency-Key is already being processed")
                i_own_key = True

            # STEP 1: Validate both accounts exist and are active (CRITICAL)
            logger.info(f"[VALIDATION] Validating from account {from_account}")
            from_account_data = await self.account_client.validate_account(from_account)

            logger.info(f"[VALIDATION] Validating to account {to_account}")
            to_account_data = await self.account_client.validate_account(to_account)

            # STEP 2: Ensure accounts are different
            logger.info(f"[VALIDATION] Checking accounts are different")
            TransferValidator.validate_different_accounts(from_account, to_account)

            # STEP 3: Verify PIN for source account
            logger.info(f"[VALIDATION] Validating PIN format")
            PINValidator.validate_pin_format(pin)

            logger.info(f"[VALIDATION] Verifying PIN for account {from_account}")
            await self.account_client.verify_pin(from_account, pin)

            # STEP 4: Validate amount
            logger.info(f"[VALIDATION] Validating amount: {amount}")
            AmountValidator.validate_transfer_amount(amount)

            # STEP 5: Check source account balance
            logger.info(f"[VALIDATION] Checking balance")
            current_balance = from_account_data.get("balance", 0)
            BalanceValidator.validate_sufficient_balance(current_balance, float(amount))

            # STEP 6: Check privilege and daily transfer limits
            logger.info(f"[VALIDATION] Checking daily transfer limits")
            privilege = from_account_data.get("privilege", "BASIC")
            daily_used = await self.limit_repo.get_daily_used_amount(from_account)
            daily_count = await self.limit_repo.get_daily_transaction_count(from_account)

            TransferLimitValidator.validate_transfer_limits(
                privilege, daily_used, daily_count, amount
            )

            # STEP 6.1: Enforce the per-transaction ceiling from the DB rule.
            # Prefer the DB transfer_limits.per_transaction_limit; fall back to
            # the in-memory settings value only when the DB has no row.
            rule = await self.limit_repo.get_transfer_rule(privilege)
            if rule and rule.get("transaction_limit") is not None:
                per_txn_limit = Decimal(str(rule["transaction_limit"]))
            else:
                fallback = settings.TRANSFER_LIMITS.get(privilege, {}).get(
                    "per_transaction_limit"
                )
                per_txn_limit = (
                    Decimal(str(fallback)) if fallback is not None else None
                )

            if per_txn_limit is not None:
                logger.info(
                    f"[VALIDATION] Enforcing per-transaction limit ₹{per_txn_limit}"
                )
                TransferLimitValidator.validate_per_transaction_limit(
                    amount, per_txn_limit
                )

            # STEP 6.5: Central Payment Gateway Validation (NEW)
            # Must happen before any financial impact
            logger.info("[GATEWAY] Contacting Central Payment Gateway for Validation...")
            
            is_approved = await self.payment_gateway_client.validate_payment(
                source_account=from_account,
                dest_account=to_account,
                amount=float(amount),
                mode=transfer_mode.value
            )

            if not is_approved:
                logger.error("[GATEWAY] Central Payment Gateway REJECTED the transaction")
                raise PaymentProcessingError("Central Payment Gateway rejected the transaction")

            logger.info("[GATEWAY] Central Payment Gateway APPROVED")

            # STEP 7: Debit source and credit destination via Account Service.
            # These are two independent calls, so the transfer must be atomic by
            # compensation: if the credit fails after the debit succeeded, we
            # reverse the debit so money is never destroyed.
            logger.info(f"[EXECUTION] Debiting source account {from_account}")
            debit_result = await self.account_client.debit_account(
                account_number=from_account,
                amount=float(amount),
                description=description or f"Transfer to {to_account}",
            )

            logger.info(f"[EXECUTION] Crediting destination account {to_account}")
            try:
                credit_result = await self.account_client.credit_account(
                    account_number=to_account,
                    amount=float(amount),
                    description=description or f"Transfer from {from_account}",
                )
            except Exception as credit_err:
                # Credit failed after a successful debit -> compensate by
                # refunding the source account so no funds are lost.
                logger.error(
                    f"[EXECUTION] Credit to {to_account} failed after debiting "
                    f"{from_account}; reversing debit. Cause: {credit_err}"
                )
                try:
                    await self.account_client.credit_account(
                        account_number=from_account,
                        amount=float(amount),
                        description=f"Reversal: failed transfer to {to_account}",
                    )
                    logger.info(f"[EXECUTION] Debit on {from_account} reversed successfully")
                except Exception as reversal_err:
                    # Reversal itself failed -> money is stranded; must be loud
                    # so it can be reconciled manually.
                    logger.critical(
                        f"[EXECUTION] CRITICAL: reversal FAILED for {from_account} "
                        f"amount {amount}. Manual reconciliation required. Cause: {reversal_err}"
                    )
                raise TransferFailedException(
                    "Transfer failed while crediting the destination account; "
                    "the source account was refunded."
                )

            # Both legs settled — money has moved. Any failure below (ledger/log)
            # must not release the idempotency key, or a retry would move it again.
            money_moved = True

            from_new_balance = debit_result.get("new_balance", 0)
            to_new_balance = credit_result.get("new_balance", 0)
            
            # Ensure balances are numeric (handle string conversion if needed)
            if isinstance(from_new_balance, str):
                from_new_balance = float(from_new_balance)
            else:
                from_new_balance = float(from_new_balance)
            
            if isinstance(to_new_balance, str):
                to_new_balance = float(to_new_balance)
            else:
                to_new_balance = float(to_new_balance)

            # STEP 8: Log transaction to database - CREATE fund_transfers record FIRST
            transaction_id = await self.transaction_repo.create_transaction(
                from_account=from_account,
                to_account=to_account,
                amount=float(amount),
                transaction_type=TransactionType.TRANSFER,
                description=description or f"Transfer from {from_account} to {to_account}",
            )

            # STEP 9: Log to transaction_logging
            # Log DEBIT for Sender (TRANSFER type)
            await self.log_repo.log_to_database(
                account_number=from_account,
                amount=float(amount),
                transaction_type=TransactionType.TRANSFER,
                reference_id=transaction_id,
                description=description,
            )
            
            # Log CREDIT for Recipient (DEPOSIT type to show as inflow)
            await self.log_repo.log_to_database(
                account_number=to_account,
                amount=float(amount),
                transaction_type=TransactionType.DEPOSIT,
                reference_id=transaction_id,
                description=f"Transfer from {from_account}",
            )

            # STEP 10: Log to file
            self.log_repo.log_to_file(
                account_number=from_account,
                amount=float(amount),
                transaction_type=TransactionType.TRANSFER,
                reference_id=transaction_id,
                description=description,
            )

            # STEP 11: Notification Service (NEW)
            try:
                from_name = from_account_data.get("name", "Account")
                to_name = to_account_data.get("name", "Account")

                # Notify Sender
                await self.notification_client.send_notification(
                    recipient=str(from_account),
                    message=f"Sent: ₹{amount} via {transfer_mode.value} to {to_name} ({to_account}). Bal: ₹{from_new_balance}",
                    type="SUCCESS",
                    mode=transfer_mode.value
                )
                # Notify Receiver
                await self.notification_client.send_notification(
                    recipient=str(to_account),
                    message=f"Received: ₹{amount} via {transfer_mode.value} from {from_name} ({from_account}). Bal: ₹{to_new_balance}",
                    type="SUCCESS",
                    mode=transfer_mode.value
                )
            except Exception as notify_err:
                logger.warning(f"[NOTIFICATION] Notification failed (Non-blocking): {notify_err}")

            logger.info(f"[SUCCESS] Transfer successful: Transaction ID {transaction_id}")

            result = {
                "status": "SUCCESS",
                "transaction_id": transaction_id,
                "from_account": from_account,
                "to_account": to_account,
                "amount": float(amount),
                "transfer_mode": transfer_mode.value,
                "transaction_type": TransactionType.TRANSFER.value,
                "description": description,
                "from_account_new_balance": float(from_new_balance),
                "to_account_new_balance": float(to_new_balance),
                "transaction_date": datetime.utcnow().isoformat(),
            }

            if idempotency_key:
                await IdempotencyRepository.complete(idempotency_key, result)

            return result

        except IdempotencyException:
            # Duplicate-in-progress: we never reserved the key here, so nothing
            # to release; just surface the 409.
            raise

        except (
            AccountNotFoundException,
            AccountNotActiveException,
            SameAccountTransferException,
            InvalidPINException,
            InvalidAmountException,
            InsufficientFundsException,
            TransferLimitExceededException,
            DailyTransactionCountExceededException,
            PaymentProcessingError,
        ):
            if i_own_key and not money_moved:
                await IdempotencyRepository.release(idempotency_key)
            raise

        except ServiceUnavailableException:
            if i_own_key and not money_moved:
                await IdempotencyRepository.release(idempotency_key)
            raise

        except Exception as e:
            # Unexpected error
            if i_own_key and not money_moved:
                await IdempotencyRepository.release(idempotency_key)
            logger.error(f"[ERROR] Transfer failed: {str(e)}")
            raise TransferFailedException(f"Transfer failed: {str(e)}")



# Singleton instance
transfer_service = TransferService()
