"""Service-unavailable exception for the transactions service.

Defines :class:`ServiceUnavailableException`, raised when a dependency required
to move money (e.g., the Account Service) is unreachable or not responding.
Part of the transactions_service exception hierarchy rooted at
:class:`TransactionException`.
"""
from .transaction_exception import TransactionException

class ServiceUnavailableException(TransactionException):
    """External service (e.g., Account Service) is unavailable."""
    
    http_code = 503
    error_code = "SERVICE_UNAVAILABLE"
