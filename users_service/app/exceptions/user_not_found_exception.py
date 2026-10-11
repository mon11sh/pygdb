"""User-not-found exception for the user management service.

Defines ``UserNotFoundException``, raised when no user matches the requested
``login_id``, returning an HTTP 404 error.
"""

from .user_management_exception_base import UserManagementException

class UserNotFoundException(UserManagementException):
    """Raised when user is not found in database."""

    def __init__(self, login_id: str):
        """Initialize UserNotFoundException."""
        super().__init__(
            status_code=404,
            detail=f"User with login_id '{login_id}' not found",
            error_code="USER_NOT_FOUND",
        )
