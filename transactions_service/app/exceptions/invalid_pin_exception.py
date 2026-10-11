"""Exception raised when a supplied account PIN is incorrect.

Defines :class:`InvalidPINException`, a domain exception in the
transactions_service exception hierarchy. It is raised when the PIN provided to
authorize a money-movement operation is invalid or does not match, mapping to
an HTTP 401 Unauthorized response.
"""
from .transaction_exception import TransactionException

class InvalidPINException(TransactionException):
    """PIN is invalid or incorrect."""
    
    http_code = 401
    error_code = "INVALID_PIN"
