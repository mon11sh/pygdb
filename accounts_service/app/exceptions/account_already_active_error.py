"""Exception raised when activating an already-active account.

Defines :class:`AccountAlreadyActiveError`, a domain error signalling that
an activation request targeted an account that is already active. Part of
the accounts service exception hierarchy rooted at :class:`AccountException`.
"""
from .account_exception import AccountException

class AccountAlreadyActiveError(AccountException):
    """Raised when trying to activate an already active account."""
    
    def __init__(self, account_number: int):
        """Build the error with a message identifying the active account.

        Args:
            account_number: Identifier of the account already active.
        """
        super().__init__(
            f"Account {account_number} is already active",
            "ACCOUNT_ALREADY_ACTIVE"
        )
