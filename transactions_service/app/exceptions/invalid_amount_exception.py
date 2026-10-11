"""Exception raised when a transaction amount is invalid.

Defines :class:`InvalidAmountException`, a domain exception in the
transactions_service exception hierarchy. It is raised when a deposit,
withdrawal, or transfer specifies a non-positive or otherwise invalid amount,
mapping to an HTTP 400 response.
"""
from .transaction_exception import TransactionException

class InvalidAmountException(TransactionException):
    """Invalid transaction amount."""
    
    http_code = 400
    error_code = "INVALID_AMOUNT"
