"""Exception raised when the upstream Account Service fails.

Defines :class:`AccountServiceException`, a domain exception in the
transactions_service exception hierarchy. It is raised when a call to the
external Account Service (for account lookup, status, or balance) returns an
error, mapping to an HTTP 502 Bad Gateway response.
"""
from .transaction_exception import TransactionException

class AccountServiceException(TransactionException):
    """Account Service returned an error."""
    
    http_code = 502
    error_code = "ACCOUNT_SERVICE_ERROR"
