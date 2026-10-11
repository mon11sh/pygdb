"""Exception raised when a transaction breaches the daily amount limit.

Defines :class:`DailyAmountLimitException`, a domain exception in the
transactions_service exception hierarchy. It is raised when the cumulative
transacted amount for an account within a single day would exceed the
configured daily amount limit, mapping to an HTTP 400 response.
"""
from .transaction_exception import TransactionException

class DailyAmountLimitException(TransactionException):
    """Daily amount limit exceeded."""
    
    http_code = 400
    error_code = "DAILY_AMOUNT_LIMIT_EXCEEDED"
