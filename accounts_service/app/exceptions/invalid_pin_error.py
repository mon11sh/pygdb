"""Exception raised when a PIN is invalid or verification fails.

Defines :class:`InvalidPinError`, a domain error signalling a failed PIN
verification or an otherwise invalid PIN. Part of the accounts service
exception hierarchy rooted at :class:`AccountException`.
"""
from .account_exception import AccountException

class InvalidPinError(AccountException):
    """Raised when PIN is invalid."""
    
    def __init__(self, message: str = "PIN verification failed"):
        """Build the error with an optional custom message.

        Args:
            message: Description of the PIN failure.
        """
        super().__init__(message, "INVALID_PIN")
