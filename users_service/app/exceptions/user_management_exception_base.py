"""Base exception type for the user management domain.

Defines ``UserManagementException``, the root of the service's custom exception
hierarchy. It extends FastAPI's ``HTTPException`` so raised errors map directly
onto HTTP responses while carrying an additional ``error_code`` for structured
client-side handling.
"""

from fastapi import HTTPException
from typing import Optional

class UserManagementException(HTTPException):
    """
    Base exception for all user management operations.

    Attributes:
        status_code: HTTP status code
        detail: Error message
        error_code: Custom error code for client handling
    """

    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str = "USER_MANAGEMENT_ERROR",
    ):
        """Initialize UserManagementException."""
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code
