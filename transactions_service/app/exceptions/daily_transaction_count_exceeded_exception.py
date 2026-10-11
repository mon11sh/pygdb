"""Exception raised when the daily transaction count limit is breached.

Defines :class:`DailyTransactionCountExceededException`, a domain exception in
the transactions_service exception hierarchy. It is raised when an account has
reached the maximum number of allowed transactions within a single day,
mapping to an HTTP 400 response.
"""
from .transaction_exception import TransactionException

class DailyTransactionCountExceededException(TransactionException):
    """Daily transaction count limit exceeded."""
    
    http_code = 400
    error_code = "DAILY_TRANSACTION_COUNT_EXCEEDED"
