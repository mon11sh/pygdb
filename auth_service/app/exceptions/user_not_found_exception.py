"""User not found exception mapping a missing account to HTTP 404."""
from .authentication_exception import AuthenticationException

class UserNotFoundException(AuthenticationException):
    """Raised when user does not exist."""

    def __init__(self, message: str = "User not found"):
        """Initialize the exception with an HTTP 404 status code.

        Args:
            message: Description of the missing-user condition. Defaults
                to "User not found".
        """
        super().__init__(message, status_code=404)
