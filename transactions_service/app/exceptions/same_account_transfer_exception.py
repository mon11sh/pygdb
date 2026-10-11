"""Same-account transfer exception for the transactions service.

Defines :class:`SameAccountTransferException`, raised when a transfer request
names the same account as both source and destination. Part of the
transactions_service exception hierarchy rooted at :class:`TransactionException`.
"""
from .transaction_exception import TransactionException

class SameAccountTransferException(TransactionException):
    """Cannot transfer to the same account."""
    
    http_code = 400
    error_code = "SAME_ACCOUNT_TRANSFER"
