"""Exception raised when a privilege level is invalid.

Defines :class:`InvalidPrivilegeError`, a domain error signalling that a
supplied privilege tier is not one of the accepted values (PREMIUM, GOLD,
or SILVER). Part of the accounts service exception hierarchy rooted at
:class:`AccountException`.
"""
from .account_exception import AccountException

class InvalidPrivilegeError(AccountException):
    """Raised when privilege level is invalid."""
    
    def __init__(self, privilege: str):
        """Build the error naming the invalid privilege and allowed values.

        Args:
            privilege: The rejected privilege tier value.
        """
        super().__init__(
            f"Invalid privilege: {privilege}. Must be PREMIUM, GOLD, or SILVER",
            "INVALID_PRIVILEGE"
        )
