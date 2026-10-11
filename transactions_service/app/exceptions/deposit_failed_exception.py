"""Exception raised when a deposit cannot be completed.

Defines :class:`DepositFailedException`, a domain exception in the
transactions_service exception hierarchy. It is raised when a deposit
operation fails to credit the target account, mapping to an HTTP 400 response.
"""
from .transaction_exception import TransactionException

class DepositFailedException(TransactionException):
    """Deposit operation failed."""
    
    http_code = 400
    error_code = "DEPOSIT_FAILED"
