"""Transfer-limit-not-found exception for the transactions service.

Defines :class:`TransferLimitNotFoundException`, raised when no transfer limit
configuration exists for the account being evaluated during a transfer. Part of
the transactions_service exception hierarchy rooted at
:class:`TransactionException`.
"""
from .transaction_exception import TransactionException

class TransferLimitNotFoundException(TransactionException):
    """Transfer limit not found for account."""
    
    http_code = 404
    error_code = "TRANSFER_LIMIT_NOT_FOUND"
