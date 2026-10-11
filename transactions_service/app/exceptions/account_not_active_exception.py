"""Exception raised when a money-movement operation targets an inactive account.

Defines :class:`AccountNotActiveException`, a domain exception in the
transactions_service exception hierarchy. It is raised when a deposit,
withdrawal, or transfer references an account whose status is not active,
mapping to an HTTP 400 response.
"""
from .transaction_exception import TransactionException

class AccountNotActiveException(TransactionException):
    """Account is not active."""
    
    http_code = 400
    error_code = "ACCOUNT_NOT_ACTIVE"
