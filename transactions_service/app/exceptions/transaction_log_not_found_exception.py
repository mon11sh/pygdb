"""Transaction-log-not-found exception for the transactions service.

Defines :class:`TransactionLogNotFoundException`, raised when a lookup for a
transaction log entry (e.g., by reference or idempotency key) yields no match.
Part of the transactions_service exception hierarchy rooted at
:class:`TransactionException`.
"""
from .transaction_exception import TransactionException

class TransactionLogNotFoundException(TransactionException):
    """Transaction log not found."""
    
    http_code = 404
    error_code = "TRANSACTION_LOG_NOT_FOUND"
