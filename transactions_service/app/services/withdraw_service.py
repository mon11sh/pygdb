"""
Withdraw Service

Handles withdrawal operations (FE010).

Business Logic:
1. Validate account via Account Service
2. Check account is active
3. Verify PIN
4. Check sufficient balance
5. Debit amount from account
6. Log transaction to DB + file
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
    WithdrawalFailedException,
    ServiceUnavailableException,
    InsufficientFundsException,
)
from app.models.enums import TransactionType
from app.validation.validators import (
    AmountValidator,
    BalanceValidator,
    PINValidator,
)
from app.integration.account_service_client import account_service_client
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.transaction_log_repository import TransactionLogRepository
from app.repositories.idempotency_repository import IdempotencyRepository
from app.exceptions.idempotency_exception import IdempotencyException
from app.integration.notification_client import notification_client

logger = logging.getLogger(__name__)


class WithdrawService:
    """Service for withdrawal operations."""

    def __init__(self, log_repo: Optional[TransactionLogRepository] = None):
        """Initialize service with repositories."""
        self.transaction_repo = TransactionRepository()
        self.log_repo = log_repo or TransactionLogRepository()
        self.account_client = account_service_client

    async def process_withdraw(
        self,
        account_number: int,
        amount: Decimal,
        pin: str,
        description: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process withdrawal operation.

        CRITICAL FLOW:
        1. Validate account exists and is active via Account Service
        2. Validate PIN format
        3. Verify PIN via Account Service
        4. Validate amount
        5. Check sufficient balance
        6. Debit account via Account Service
        7. Log transaction to DB and file
        8. Return transaction details

        Args:
            account_number: Account to withdraw from
            amount: Withdrawal amount
            pin: Account PIN
            description: Optional description

        Returns:
            Dict with transaction details

        Raises:
            AccountNotFoundException: If account doesn't exist
            AccountNotActiveException: If account is not active
            InvalidPINException: If PIN is invalid
            InvalidAmountException: If amount is invalid
            InsufficientFundsException: If balance is insufficient
            WithdrawalFailedException: If withdrawal fails
            ServiceUnavailableException: If Account Service is down
        """
        i_own_key = False
        money_moved = False  # once True, a failure must NOT release the key (would allow a re-run = double-spend)
        try:
            # STEP 0: Idempotency (insert-first). A completed key replays its
            # stored result; a duplicate still in progress is rejected (409).
            if idempotency_key:
                completed = await IdempotencyRepository.get_completed_response(idempotency_key)
                if completed is not None:
                    logger.info(f"↩️ Idempotent replay for key {idempotency_key}; returning stored withdrawal result")
                    return completed
                if not await IdempotencyRepository.reserve(idempotency_key, "WITHDRAWAL"):
                    completed = await IdempotencyRepository.get_completed_response(idempotency_key)
                    if completed is not None:
                        return completed
                    raise IdempotencyException("A withdrawal with this Idempotency-Key is already being processed")
                i_own_key = True

            # STEP 1: Validate account exists and is active (CRITICAL)
            logger.info(f"📋 Validating account {account_number}")
            account_data = await self.account_client.validate_account(account_number)

            # STEP 2: Validate PIN format
            logger.info(f"🔐 Validating PIN format")
            PINValidator.validate_pin_format(pin)

            # STEP 3: Verify PIN via Account Service
            logger.info(f"🔒 Verifying PIN")
            await self.account_client.verify_pin(account_number, pin)

            # STEP 4: Validate amount
            logger.info(f"💰 Validating amount: ₹{amount}")
            AmountValidator.validate_withdrawal_amount(amount)

            # STEP 5: Check sufficient balance
            logger.info(f"💵 Checking balance")
            current_balance = account_data.get("balance", 0)
            BalanceValidator.validate_sufficient_balance(current_balance, float(amount))

            # STEP 6: Debit account via Account Service
            logger.info(f"💳 Debiting account {account_number}")
            debit_result = await self.account_client.debit_account(
                account_number=account_number,
                amount=float(amount),
                description=description or "Withdrawal",
            )
            money_moved = True  # funds debited — do not release the idempotency key past this point

            # Ensure new_balance is numeric (handle string conversion if needed)
            new_balance = debit_result.get("new_balance", 0)
            if isinstance(new_balance, str):
                new_balance = float(new_balance)
            else:
                new_balance = float(new_balance)

            # STEP 7: Log transaction to database (Primary Record)
            transaction_id = await self.log_repo.log_to_database(
                account_number=account_number,
                amount=float(amount),
                transaction_type=TransactionType.WITHDRAWAL,
                reference_id=None,
                description=description,
            )
            
            if not transaction_id:
                raise WithdrawalFailedException("Failed to create transaction log")

            # STEP 8: Log to file
            self.log_repo.log_to_file(
                account_number=account_number,
                amount=float(amount),
                transaction_type=TransactionType.WITHDRAWAL,
                reference_id=transaction_id,
                description=description,
            )

            logger.info(f"✅ Withdrawal successful: Transaction ID {transaction_id}")

            # Send Notification
            try:
                name = account_data.get("name", "Account")
                await notification_client.send_notification(
                    recipient=str(account_number),
                    message=f"Success! ₹{amount} withdrawn via ATM from {name} ({account_number}). New balance: ₹{new_balance}.",
                    type="SUCCESS",
                    mode="ATM"
                )
            except Exception as e:
                logger.warning(f"Failed to send withdrawal notification: {e}")

            result = {
                "status": "SUCCESS",
                "transaction_id": transaction_id,
                "account_number": account_number,
                "amount": float(amount),
                "transaction_type": TransactionType.WITHDRAWAL.value,
                "description": description,
                "new_balance": float(new_balance),
                "transaction_date": datetime.utcnow().isoformat(),
            }

            if idempotency_key:
                await IdempotencyRepository.complete(idempotency_key, result)

            return result

        except IdempotencyException:
            raise

        except (
            AccountNotFoundException,
            AccountNotActiveException,
            InvalidPINException,
            InvalidAmountException,
            InsufficientFundsException,
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
            logger.error(f"❌ Withdrawal failed: {str(e)}")
            raise WithdrawalFailedException(f"Withdrawal failed: {str(e)}")



# Singleton instance
withdraw_service = WithdrawService()
