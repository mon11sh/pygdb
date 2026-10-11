"""Source-account-inactive exception for the transactions service.

Defines :class:`SourceAccountInactiveException`, raised when a debit or transfer
is attempted from a source account that is not active (e.g., frozen or closed).
Part of the transactions_service exception hierarchy rooted at
:class:`TransactionException`.
"""
from .transaction_exception import TransactionException

class SourceAccountInactiveException(TransactionException):
    """Source account is inactive."""
    
    http_code = 400
    error_code = "SOURCE_ACCOUNT_INACTIVE"
