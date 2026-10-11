"""Invalid token exception mapping a malformed/unverifiable JWT to HTTP 401."""
from .authentication_exception import AuthenticationException

class InvalidTokenException(AuthenticationException):
    """Raised when JWT token is invalid."""

    def __init__(self, message: str = "Invalid token"):
        """Initialize the exception with an HTTP 401 status code.

        Args:
            message: Description of the token failure. Defaults to
                "Invalid token".
        """
        super().__init__(message, status_code=401)
