"""
Authentication Exceptions
"""
class AuthenticationException(Exception):
    """Base exception for authentication errors."""
    
    def __init__(self, message: str, status_code: int = 400):
        """Initialize the authentication exception.

        Args:
            message: Human-readable description of the error condition.
            status_code: HTTP status code associated with the error.
                Defaults to 400 (Bad Request).
        """
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)
