"""Token expired exception mapping an expired JWT to HTTP 401."""
from .authentication_exception import AuthenticationException

class TokenExpiredException(AuthenticationException):
    """Raised when JWT token is expired."""

    def __init__(self, message: str = "Token has expired"):
        """Initialize the exception with an HTTP 401 status code.

        Args:
            message: Description of the expiry. Defaults to
                "Token has expired".
        """
        super().__init__(message, status_code=401)
