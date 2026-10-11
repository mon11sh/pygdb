"""Base exception type for the accounts service domain.

Defines :class:`AccountException`, the root of the service's custom
exception hierarchy. Every specialized account error subclasses this type,
inheriting a human-readable ``message`` and a machine-readable
``error_code`` that API error handlers translate into HTTP responses.
"""

class AccountException(Exception):
    """Base exception for all account-related errors."""
    
    def __init__(self, message: str, error_code: str = "ACCOUNT_ERROR"):
        """
        Initialize account exception.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
        """
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)
