"""Exception raised when a balance operation is invalid.

Defines :class:`InvalidBalanceError`, a domain error signalling an invalid
balance-related operation (for example a negative or otherwise disallowed
balance). Part of the accounts service exception hierarchy rooted at
:class:`AccountException`.
"""
from .account_exception import AccountException

class InvalidBalanceError(AccountException):
    """Raised when balance operation is invalid."""
    
    def __init__(self, message: str = "Invalid balance operation"):
        """Build the error with an optional custom message.

        Args:
            message: Description of the invalid balance operation.
        """
        super().__init__(message, "INVALID_BALANCE")
