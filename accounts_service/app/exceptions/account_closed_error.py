"""Exception raised when operating on a closed account.

Defines :class:`AccountClosedError`, a domain error signalling that an
operation was attempted on an account that has been closed. Part of the
accounts service exception hierarchy rooted at :class:`AccountException`.
"""
from .account_exception import AccountException

class AccountClosedError(AccountException):
    """Raised when trying to operate on closed account."""
    
    def __init__(self, account_number: int):
        """Build the error with a message identifying the closed account.

        Args:
            account_number: Identifier of the closed account.
        """
        super().__init__(
            f"Account {account_number} is closed",
            "ACCOUNT_CLOSED"
        )
