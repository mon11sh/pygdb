"""Exception raised when both transfer accounts are inactive.

Defines :class:`BothAccountsInactiveException`, a domain exception in the
transactions_service exception hierarchy. It is raised during a transfer when
neither the source nor the destination account is active, mapping to an
HTTP 400 response.
"""
from .transaction_exception import TransactionException

class BothAccountsInactiveException(TransactionException):
    """Both source and destination accounts are inactive."""
    
    http_code = 400
    error_code = "BOTH_ACCOUNTS_INACTIVE"
