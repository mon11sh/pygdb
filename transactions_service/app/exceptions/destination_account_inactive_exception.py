"""Exception raised when a transfer's destination account is inactive.

Defines :class:`DestinationAccountInactiveException`, a domain exception in the
transactions_service exception hierarchy. It is raised during a transfer when
the destination (credit) account is not active, mapping to an HTTP 400
response.
"""
from .transaction_exception import TransactionException

class DestinationAccountInactiveException(TransactionException):
    """Destination account is inactive."""
    
    http_code = 400
    error_code = "DESTINATION_ACCOUNT_INACTIVE"
