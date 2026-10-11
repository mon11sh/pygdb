"""
Deposit Service

Handles deposit operations (FE011).

Business Logic:
1. Validate account via Account Service
2. Check account is active
3. Credit amount to account
4. Log transaction to DB + file
"""

import logging
from typing import Dict, Any, Optional
from decimal import Decimal
from datetime import datetime

from app.exceptions.transaction_exceptions import (
    AccountNotFoundException,
    AccountNotActiveException,
    InvalidAmountException,
    DepositFailedException,
    ServiceUnavailableException,
)
from app.models.enums import TransactionType
from app.validation.validators import AmountValidator
from app.integration.account_service_client import account_service_client
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.transaction_log_repository import TransactionLogRepository
from app.repositories.idempotency_repository import IdempotencyRepository
from app.exceptions.idempotency_exception import IdempotencyException
from app.integration.notification_client import notification_client

logger = logging.getLogger(__name__)


class DepositService:
    """Service for deposit operations."""

    def __init__(self, log_repo: Optional[TransactionLogRepository] = None):
        """Initialize service with repositories."""
        self.transaction_repo = TransactionRepository()
        self.log_repo = log_repo or TransactionLogRepository()
        self.account_client = account_service_client

    async def process_deposit(
        self,
        account_number: int,
        amount: Decimal,
        description: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process deposit operation.

        CRITICAL FLOW:
        1. Validate account exists and is active via Account Service
        2. Validate amount
        3. Credit account via Account Service
        4. Create transaction record
        5. Log transaction to file
        6. Return transaction details

        Args:
            account_number: Account to deposit to
            amount: Deposit amount
            description: Optional description

        Returns:
            Dict with transaction details

        Raises:
            AccountNotFoundException: If account doesn't exist
            AccountNotActiveException: If account is not active
            InvalidAmountException: If amount is invalid
            DepositFailedException: If deposit fails
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
                    logger.info(f"↩️ Idempotent replay for key {idempotency_key}; returning stored deposit result")
                    return completed
                if not await IdempotencyRepository.reserve(idempotency_key, "DEPOSIT"):
                    completed = await IdempotencyRepository.get_completed_response(idempotency_key)
                    if completed is not None:
                        return completed
                    raise IdempotencyException("A deposit with this Idempotency-Key is already being processed")
                i_own_key = True

            # STEP 1: Validate account exists and is active (CRITICAL)
            logger.info(f"📋 Validating account {account_number}")
            account_data = await self.account_client.validate_account(account_number)

            # STEP 2: Validate amount
            logger.info(f"💰 Validating amount: ₹{amount}")
            AmountValidator.validate_deposit_amount(amount)

            # STEP 3: Credit account via Account Service
            logger.info(f"💳 Crediting account {account_number}")
            credit_result = await self.account_client.credit_account(
                account_number=account_number,
                amount=float(amount),
                description=description or "Deposit",
            )
            money_moved = True  # funds credited — do not release the idempotency key past this point

            # Verify credit_result is a dict before calling .get()
            if not isinstance(credit_result, dict):
                logger.error(f"❌ ERROR: credit_result is not a dict! Type: {type(credit_result)}, Value: {credit_result}")
                raise TypeError(f"Expected dict from credit_account, got {type(credit_result)}")
            
            new_balance = credit_result.get("new_balance", 0)
            # Ensure new_balance is numeric (handle string conversion if needed)
            if isinstance(new_balance, str):
                new_balance = float(new_balance)
            else:
                new_balance = float(new_balance)

            # STEP 4: Log transaction to database (Primary Record)
            transaction_id = await self.log_repo.log_to_database(
                account_number=account_number,
                amount=amount,
                transaction_type=TransactionType.DEPOSIT,
                reference_id=None,  # Not needed as this is the primary record
                description=description,
            )
            
            if not transaction_id:
                raise DepositFailedException("Failed to create transaction log")

            # STEP 5: Log to file
            self.log_repo.log_to_file(
                account_number=account_number,
                amount=amount,
                transaction_type=TransactionType.DEPOSIT,
                reference_id=transaction_id,
                description=description,
            )

            logger.info(f"✅ Deposit successful: Transaction ID {transaction_id}")

            # Send Notification
            try:
                name = account_data.get("name", "Account")
                await notification_client.send_notification(
                    recipient=str(account_number),
                    message=f"Success! ₹{amount} deposited via DIRECT to {name} ({account_number}). New balance: ₹{new_balance}.",
                    type="SUCCESS",
                    mode="DIRECT"
                )
            except Exception as e:
                logger.warning(f"Failed to send deposit notification: {e}")

            result = {
                "status": "SUCCESS",
                "transaction_id": transaction_id,
                "account_number": account_number,
                "amount": float(amount),
                "transaction_type": TransactionType.DEPOSIT.value,
                "description": description,
                "new_balance": float(new_balance),
                "transaction_date": datetime.utcnow().isoformat(),
            }

            # Record the result so a replay of this idempotency key is a no-op.
            if idempotency_key:
                await IdempotencyRepository.complete(idempotency_key, result)

            return result

        except IdempotencyException:
            raise

        except (
            AccountNotFoundException,
            AccountNotActiveException,
            InvalidAmountException,
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
            logger.error(f"❌ Deposit failed: {str(e)}", exc_info=True)
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise DepositFailedException(f"Deposit failed: {str(e)}")



# Singleton instance
deposit_service = DepositService()
