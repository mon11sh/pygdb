"""Logging exception for the transactions service.

Defines :class:`LoggingException`, raised when the service fails to persist an
audit/transaction log entry for a money-movement operation. Part of the
transactions_service exception hierarchy rooted at :class:`TransactionException`.
"""
from .transaction_exception import TransactionException

class LoggingException(TransactionException):
    """Transaction logging failed."""
    
    http_code = 500
    error_code = "LOGGING_ERROR"
