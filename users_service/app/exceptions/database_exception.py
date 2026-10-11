"""Database failure exception for the user management service.

Defines ``DatabaseException``, raised when an underlying database operation
fails, surfacing the failing operation and its cause as an HTTP 500 error.
"""

from .user_management_exception_base import UserManagementException

class DatabaseException(UserManagementException):
    """Raised when database operation fails."""

    def __init__(self, operation: str, reason: str):
        """Initialize DatabaseException."""
        super().__init__(
            status_code=500,
            detail=f"Database error during {operation}: {reason}",
            error_code="DATABASE_ERROR",
        )
