"""Exception raised when transaction parameters are invalid.

Defines :class:`InvalidTransactionException`, a domain exception in the
transactions_service exception hierarchy. It is raised when a money-movement
request carries invalid or inconsistent parameters that fail domain
validation, mapping to an HTTP 400 response.
"""
from .transaction_exception import TransactionException

class InvalidTransactionException(TransactionException):
    """Invalid transaction parameters."""
    
    http_code = 400
    error_code = "INVALID_TRANSACTION"
