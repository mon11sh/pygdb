"""Exception raised when operating on an inactive account.

Defines :class:`AccountInactiveError`, a domain error signalling that an
operation was attempted on an account that is currently inactive. Part of
the accounts service exception hierarchy rooted at :class:`AccountException`.
"""
from .account_exception import AccountException

class AccountInactiveError(AccountException):
    """Raised when trying to operate on inactive account."""
    
    def __init__(self, account_number: int):
        """Build the error with a message identifying the inactive account.

        Args:
            account_number: Identifier of the inactive account.
        """
        super().__init__(
            f"Account {account_number} is inactive",
            "ACCOUNT_INACTIVE"
        )
