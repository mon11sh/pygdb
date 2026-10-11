"""Invalid transfer mode exception for the transactions service.

Defines :class:`InvalidTransferModeException`, raised when a money-movement
request specifies a transfer mode (e.g., NEFT, IMPS, internal) that is not
recognized or supported by the service. Part of the transactions_service
exception hierarchy rooted at :class:`TransactionException`.
"""
from .transaction_exception import TransactionException

class InvalidTransferModeException(TransactionException):
    """Invalid transfer mode specified."""
    
    http_code = 400
    error_code = "INVALID_TRANSFER_MODE"
