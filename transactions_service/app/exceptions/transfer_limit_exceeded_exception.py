"""Transfer-limit-exceeded exception for the transactions service.

Defines :class:`TransferLimitExceededException`, raised when a transfer would
push an account past its configured daily transfer limit. Part of the
transactions_service exception hierarchy rooted at :class:`TransactionException`.
"""
from .transaction_exception import TransactionException

class TransferLimitExceededException(TransactionException):
    """Daily transfer limit exceeded."""
    
    http_code = 400
    error_code = "TRANSFER_LIMIT_EXCEEDED"
