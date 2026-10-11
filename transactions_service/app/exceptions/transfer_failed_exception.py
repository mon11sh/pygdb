"""Transfer-failed exception for the transactions service.

Defines :class:`TransferFailedException`, raised when a fund transfer between
accounts cannot be completed. Part of the transactions_service exception
hierarchy rooted at :class:`TransactionException`.
"""
from .transaction_exception import TransactionException

class TransferFailedException(TransactionException):
    """Transfer operation failed."""
    
    http_code = 400
    error_code = "TRANSFER_FAILED"
