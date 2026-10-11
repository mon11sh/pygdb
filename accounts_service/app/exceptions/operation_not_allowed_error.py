"""Exception raised when an operation is not permitted on an account.

Defines :class:`OperationNotAllowedError`, a domain error signalling that a
requested operation is disallowed for the account, along with the reason.
Part of the accounts service exception hierarchy rooted at
:class:`AccountException`.
"""
from .account_exception import AccountException

class OperationNotAllowedError(AccountException):
    """Raised when operation is not allowed on account."""
    
    def __init__(self, account_number: int, reason: str):
        """Build the error identifying the account and the disallowed reason.

        Args:
            account_number: Identifier of the account the operation targeted.
            reason: Explanation of why the operation is not allowed.
        """
        super().__init__(
            f"Operation not allowed on account {account_number}: {reason}",
            "OPERATION_NOT_ALLOWED"
        )
