"""Service unavailable exception mapping a dependency outage to HTTP 503."""
from .authentication_exception import AuthenticationException

class ServiceUnavailableException(AuthenticationException):
    """Raised when dependent service (User Service) is unavailable."""

    def __init__(self, message: str = "User service is unavailable"):
        """Initialize the exception with an HTTP 503 status code.

        Args:
            message: Description of the outage. Defaults to
                "User service is unavailable".
        """
        super().__init__(message, status_code=503)
