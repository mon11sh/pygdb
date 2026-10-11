"""Transaction-logging exception for the transactions service.

Defines :class:`TransactionLoggingException`, raised when a transaction logging
operation fails while recording a money-movement event. Part of the
transactions_service exception hierarchy rooted at :class:`TransactionException`.
"""
from .transaction_exception import TransactionException

class TransactionLoggingException(TransactionException):
    """Transaction logging operation failed."""
    
    http_code = 500
    error_code = "TRANSACTION_LOGGING_ERROR"
