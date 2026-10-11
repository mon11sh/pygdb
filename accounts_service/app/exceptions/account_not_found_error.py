"""Exception raised when a requested account does not exist.

Defines :class:`AccountNotFoundError`, a domain error signalling that no
account matches the supplied account number. Part of the accounts service
exception hierarchy rooted at :class:`AccountException`.
"""
from .account_exception import AccountException

class AccountNotFoundError(AccountException):
    """Raised when account does not exist."""
    
    def __init__(self, account_number: int):
        """Build the error with a message identifying the missing account.

        Args:
            account_number: Identifier of the account that was not found.
        """
        super().__init__(
            f"Account {account_number} not found",
            "ACCOUNT_NOT_FOUND"
        )
