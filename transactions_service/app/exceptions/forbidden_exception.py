"""Exception raised when a caller lacks permission for an operation.

Defines :class:`ForbiddenException`, a domain exception in the
transactions_service exception hierarchy. It is raised when an authenticated
user attempts a money-movement operation they are not authorized to perform
(for example, acting on another user's account), mapping to an HTTP 403
response.
"""
from .transaction_exception import TransactionException

class ForbiddenException(TransactionException):
    """User does not have permission for this operation."""
    
    http_code = 403
    error_code = "FORBIDDEN"
