"""Base exception definitions for the transactions service.

Defines :class:`TransactionException`, the root of the transactions_service
exception hierarchy. All money-movement errors (deposits, withdrawals,
transfers, limits, idempotency) subclass this type and inherit its
``http_code``/``error_code`` mapping used to render consistent API error
responses.
"""
from typing import Optional

class TransactionException(Exception):
    """Base exception for transaction service."""
    
    http_code: int = 400
    error_code: str = "TRANSACTION_ERROR"
    
    def __init__(self, message: str, error_code: Optional[str] = None, http_code: Optional[int] = None):
        """
        Initialize transaction exception.
        
        Args:
            message: Human-readable error message
            error_code: Error code for categorization
            http_code: HTTP status code
        """
        super().__init__(message)
        self.message = message
        if error_code:
            self.error_code = error_code
        if http_code:
            self.http_code = http_code
