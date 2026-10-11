"""User inactive exception mapping a disabled account to HTTP 403."""
from .authentication_exception import AuthenticationException

class UserInactiveException(AuthenticationException):
    """Raised when user account is inactive."""

    def __init__(self, message: str = "User account is inactive"):
        """Initialize the exception with an HTTP 403 status code.

        Args:
            message: Description of the inactive-account condition.
                Defaults to "User account is inactive".
        """
        super().__init__(message, status_code=403)
