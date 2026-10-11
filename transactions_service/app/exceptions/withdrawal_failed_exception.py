"""Withdrawal-failed exception for the transactions service.

Defines :class:`WithdrawalFailedException`, raised when a withdrawal (debit)
operation against an account cannot be completed. Part of the
transactions_service exception hierarchy rooted at :class:`TransactionException`.
"""
from .transaction_exception import TransactionException

class WithdrawalFailedException(TransactionException):
    """Withdrawal operation failed."""
    
    http_code = 400
    error_code = "WITHDRAWAL_FAILED"
