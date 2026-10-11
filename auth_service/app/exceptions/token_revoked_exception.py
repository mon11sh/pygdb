"""Token revoked exception mapping a blacklisted JWT to HTTP 401."""
from .authentication_exception import AuthenticationException

class TokenRevokedException(AuthenticationException):
    """Raised when JWT token has been revoked."""

    def __init__(self, message: str = "Token has been revoked"):
        """Initialize the exception with an HTTP 401 status code.

        Args:
            message: Description of the revocation. Defaults to
                "Token has been revoked".
        """
        super().__init__(message, status_code=401)
