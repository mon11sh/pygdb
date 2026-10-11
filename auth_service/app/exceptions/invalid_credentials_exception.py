"""Invalid credentials exception mapping a failed login to HTTP 401."""
from .authentication_exception import AuthenticationException

class InvalidCredentialsException(AuthenticationException):
    """Raised when login credentials are invalid."""

    def __init__(self, message: str = "Invalid login credentials"):
        """Initialize the exception with an HTTP 401 status code.

        Args:
            message: Description of the credential failure. Defaults to
                "Invalid login credentials".
        """
        super().__init__(message, status_code=401)
