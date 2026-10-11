"""Exception raised when deactivating an already-inactive account.

Defines :class:`AccountAlreadyInactiveError`, a domain error signalling
that a deactivation request targeted an account that is already inactive.
Part of the accounts service exception hierarchy rooted at
:class:`AccountException`.
"""
from .account_exception import AccountException

class AccountAlreadyInactiveError(AccountException):
    """Raised when trying to deactivate an already inactive account."""
    
    def __init__(self, account_number: int):
        """Build the error with a message identifying the inactive account.

        Args:
            account_number: Identifier of the account already inactive.
        """
        super().__init__(
            f"Account {account_number} is already inactive",
            "ACCOUNT_ALREADY_INACTIVE"
        )
