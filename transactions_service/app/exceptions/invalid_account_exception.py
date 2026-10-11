"""Exception raised when an account identifier is invalid or malformed.

Defines :class:`InvalidAccountException`, a domain exception in the
transactions_service exception hierarchy. It is raised when an account number
supplied to a money-movement operation is malformed or otherwise invalid,
mapping to an HTTP 400 response.
"""
from .transaction_exception import TransactionException

class InvalidAccountException(TransactionException):
    """Account is invalid or malformed."""
    
    http_code = 400
    error_code = "INVALID_ACCOUNT"
