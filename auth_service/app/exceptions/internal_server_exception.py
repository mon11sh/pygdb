"""Internal server exception mapping an unexpected error to HTTP 500."""
from .authentication_exception import AuthenticationException

class InternalServerException(AuthenticationException):
    """Raised for unexpected internal errors."""

    def __init__(self, message: str = "Internal server error"):
        """Initialize the exception with an HTTP 500 status code.

        Args:
            message: Description of the internal error. Defaults to
                "Internal server error".
        """
        super().__init__(message, status_code=500)
