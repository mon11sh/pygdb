"""Exception raised when an account type is invalid.

Defines :class:`InvalidAccountTypeError`, a domain error signalling that a
supplied account type is not one of the accepted values (SAVINGS or
CURRENT). Part of the accounts service exception hierarchy rooted at
:class:`AccountException`.
"""
from .account_exception import AccountException

class InvalidAccountTypeError(AccountException):
    """Raised when account type is invalid."""
    
    def __init__(self, account_type: str):
        """Build the error naming the invalid type and the allowed values.

        Args:
            account_type: The rejected account type value.
        """
        super().__init__(
            f"Invalid account type: {account_type}. Must be SAVINGS or CURRENT",
            "INVALID_ACCOUNT_TYPE"
        )
