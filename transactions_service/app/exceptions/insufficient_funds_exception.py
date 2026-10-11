"""Exception raised when an account has insufficient balance.

Defines :class:`InsufficientFundsException`, a domain exception in the
transactions_service exception hierarchy. It is raised when a withdrawal or
transfer would reduce the source account's balance below the permitted
minimum, mapping to an HTTP 400 response.
"""
from .transaction_exception import TransactionException

class InsufficientFundsException(TransactionException):
    """Insufficient balance for transaction."""
    
    http_code = 400
    error_code = "INSUFFICIENT_FUNDS"
