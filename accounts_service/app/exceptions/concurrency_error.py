"""Exception raised when a concurrent operation conflict occurs.

Defines :class:`ConcurrencyError`, a domain error signalling that a
simultaneous operation on the same account produced a conflict and the
caller should retry. Part of the accounts service exception hierarchy
rooted at :class:`AccountException`.
"""
from .account_exception import AccountException

class ConcurrencyError(AccountException):
    """Raised when concurrent operation causes conflict."""
    
    def __init__(self, account_number: int):
        """Build the error with a retry-oriented message for the account.

        Args:
            account_number: Identifier of the account under contention.
        """
        super().__init__(
            f"Concurrent operation on account {account_number}. Please retry",
            "CONCURRENCY_ERROR"
        )
