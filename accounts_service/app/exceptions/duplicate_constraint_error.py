"""Exception raised when a unique database constraint is violated.

Defines :class:`DuplicateConstraintError`, a domain error signalling that
an operation violated a uniqueness constraint. Part of the accounts
service exception hierarchy rooted at :class:`AccountException`.
"""
from .account_exception import AccountException

class DuplicateConstraintError(AccountException):
    """Raised when unique constraint is violated."""
    
    def __init__(self, constraint: str):
        """Build the error naming the violated uniqueness constraint.

        Args:
            constraint: Name of the unique constraint that was violated.
        """
        super().__init__(
            f"Duplicate value violates constraint: {constraint}",
            "DUPLICATE_CONSTRAINT"
        )
