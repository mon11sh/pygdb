"""Exception raised when a referenced account cannot be located.

Defines :class:`AccountNotFoundException`, a domain exception in the
transactions_service exception hierarchy. It is raised when a deposit,
withdrawal, or transfer references an account that does not exist, mapping
to an HTTP 404 response.
"""
from .transaction_exception import TransactionException

class AccountNotFoundException(TransactionException):
    """Account does not exist."""
    
    http_code = 404
    error_code = "ACCOUNT_NOT_FOUND"
