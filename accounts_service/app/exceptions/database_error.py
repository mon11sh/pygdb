"""Exception raised when a database operation fails.

Defines :class:`DatabaseError`, a domain error wrapping lower-level
persistence failures with a service-level message and error code. Part of
the accounts service exception hierarchy rooted at :class:`AccountException`.
"""
from .account_exception import AccountException

class DatabaseError(AccountException):
    """Raised when database operation fails."""
    
    def __init__(self, message: str):
        """Build the error, prefixing the given detail with "Database error".

        Args:
            message: Detail describing the underlying database failure.
        """
        super().__init__(
            f"Database error: {message}",
            "DATABASE_ERROR"
        )
