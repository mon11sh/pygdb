"""
Validation Modules for Transaction Service

Validates:
- Account existence and status
- Balance sufficiency
- Transfer limits
- Transaction amounts
"""

from decimal import Decimal
from typing import Dict, Any
from app.exceptions.transaction_exceptions import (
    InvalidAmountException,
    InvalidPINException,
    TransferLimitExceededException,
    DailyTransactionCountExceededException,
    SameAccountTransferException,
    InsufficientFundsException,
)
from app.config.settings import settings


class AmountValidator:
    """Validates transaction amounts."""

    @staticmethod
    def validate_deposit_amount(amount: Decimal) -> None:
        """
        Validate deposit amount.
        
        Args:
            amount: Amount to validate
            
        Raises:
            InvalidAmountException: If amount is invalid
        """
        if amount <= 0:
            raise InvalidAmountException("Amount must be greater than 0")
        
        if amount > Decimal(settings.MAXIMUM_TRANSACTION_AMOUNT):
            raise InvalidAmountException(
                f"Amount exceeds maximum of ₹{settings.MAXIMUM_TRANSACTION_AMOUNT}"
            )

    @staticmethod
    def validate_withdrawal_amount(amount: Decimal) -> None:
        """Validate withdrawal amount."""
        AmountValidator.validate_deposit_amount(amount)

    @staticmethod
    def validate_transfer_amount(amount: Decimal) -> None:
        """Validate transfer amount."""
        AmountValidator.validate_deposit_amount(amount)


class BalanceValidator:
    """Validates account balance for transactions."""

    @staticmethod
    def validate_sufficient_balance(
        current_balance,
        required_amount
    ) -> None:
        """
        Check if account has sufficient balance.

        Compares as Decimal so float representation error (e.g. 0.1 + 0.2)
        cannot wrongly pass or fail a balance check.

        Args:
            current_balance: Current account balance (Decimal/float/str)
            required_amount: Amount required (Decimal/float/str)

        Raises:
            InsufficientFundsException: If balance is insufficient
        """
        available = Decimal(str(current_balance))
        required = Decimal(str(required_amount))
        if available < required:
            raise InsufficientFundsException(
                f"Insufficient balance. Available: ₹{available}, "
                f"Required: ₹{required}"
            )


class PINValidator:
    """Validates PIN format and correctness."""

    @staticmethod
    def validate_pin_format(pin: str) -> None:
        """
        Validate PIN format (numeric, correct length).
        
        Args:
            pin: PIN to validate
            
        Raises:
            InvalidPINException: If PIN format is invalid
        """
        if not pin or len(pin) != settings.PIN_LENGTH:
            raise InvalidPINException(
                f"PIN must be {settings.PIN_LENGTH} digits"
            )
        
        if not pin.isdigit():
            raise InvalidPINException("PIN must contain only digits")


class TransferLimitValidator:
    """Validates transfer limits based on privilege level."""

    @staticmethod
    def validate_daily_limit(
        privilege_level: str,
        daily_used: Decimal,
        transfer_amount: Decimal
    ) -> None:
        """
        Validate transfer doesn't exceed daily limit.
        
        Args:
            privilege_level: Account privilege (PREMIUM/GOLD/SILVER/BASIC)
            daily_used: Amount already used today
            transfer_amount: Amount to transfer
            
        Raises:
            TransferLimitExceededException: If limit is exceeded
        """
        limits = settings.TRANSFER_LIMITS.get(privilege_level, {})
        daily_limit = Decimal(str(limits.get("daily_limit", 0)))
        
        total_after_transfer = daily_used + transfer_amount
        
        if total_after_transfer > daily_limit:
            remaining = daily_limit - daily_used
            raise TransferLimitExceededException(
                f"Transfer limit exceeded. Daily limit: ₹{daily_limit}, "
                f"Used: ₹{daily_used}, Remaining: ₹{remaining}"
            )

    @staticmethod
    def validate_daily_transaction_count(
        privilege_level: str,
        transaction_count_today: int
    ) -> None:
        """
        Validate transaction count doesn't exceed daily limit.
        
        Args:
            privilege_level: Account privilege level
            transaction_count_today: Number of transactions done today
            
        Raises:
            DailyTransactionCountExceededException: If count limit exceeded
        """
        limits = settings.TRANSFER_LIMITS.get(privilege_level, {})
        max_count = limits.get("daily_transaction_count", 0)
        
        if transaction_count_today >= max_count:
            raise DailyTransactionCountExceededException(
                f"Daily transaction limit exceeded. Limit: {max_count}, "
                f"Used: {transaction_count_today}"
            )

    @staticmethod
    def validate_per_transaction_limit(
        transfer_amount: Decimal,
        per_transaction_limit: Decimal
    ) -> None:
        """
        Validate a single transfer does not exceed the per-transaction ceiling.

        The ceiling is sourced from the DB transfer_limits rule
        (per_transaction_limit), preferred over the in-memory settings fallback.

        Args:
            transfer_amount: Amount to transfer
            per_transaction_limit: Maximum allowed for a single transfer

        Raises:
            TransferLimitExceededException: If the amount exceeds the ceiling
        """
        ceiling = Decimal(str(per_transaction_limit))
        if transfer_amount > ceiling:
            raise TransferLimitExceededException(
                f"Transfer amount ₹{transfer_amount} exceeds the per-transaction "
                f"limit of ₹{ceiling}"
            )

    @staticmethod
    def validate_transfer_limits(
        privilege_level: str,
        daily_used: Decimal,
        transaction_count_today: int,
        transfer_amount: Decimal
    ) -> None:
        """
        Validate all transfer limits at once.
        
        Args:
            privilege_level: Account privilege level
            daily_used: Amount used today
            transaction_count_today: Transactions done today
            transfer_amount: Amount to transfer
            
        Raises:
            Various exceptions if limits are exceeded
        """
        TransferLimitValidator.validate_daily_limit(
            privilege_level, daily_used, transfer_amount
        )
        TransferLimitValidator.validate_daily_transaction_count(
            privilege_level, transaction_count_today
        )


class TransferValidator:
    """Validates transfer operations."""

    @staticmethod
    def validate_different_accounts(
        from_account: int,
        to_account: int
    ) -> None:
        """
        Ensure from and to accounts are different.
        
        Args:
            from_account: Source account
            to_account: Destination account
            
        Raises:
            SameAccountTransferException: If accounts are the same
        """
        if from_account == to_account:
            raise SameAccountTransferException(
                "Cannot transfer to the same account"
            )
