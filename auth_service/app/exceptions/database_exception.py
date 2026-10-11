"""Database exception mapping a persistence failure to HTTP 500."""
from .authentication_exception import AuthenticationException

class DatabaseException(AuthenticationException):
    """Raised when database operation fails."""

    def __init__(self, message: str = "Database operation failed"):
        """Initialize the exception with an HTTP 500 status code.

        Args:
            message: Description of the database failure. Defaults to
                "Database operation failed".
        """
        super().__init__(message, status_code=500)
