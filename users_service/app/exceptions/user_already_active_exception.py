"""User-already-active exception for the user management service.

Defines ``UserAlreadyActiveException``, raised when an activation is requested
for a user that is already active, returning an HTTP 400 error.
"""

from .user_management_exception_base import UserManagementException

class UserAlreadyActiveException(UserManagementException):
    """Raised when attempting to activate an already active user."""

    def __init__(self, login_id: str):
        """Initialize UserAlreadyActiveException."""
        super().__init__(
            status_code=400,
            detail=f"User with login_id '{login_id}' is already active",
            error_code="USER_ALREADY_ACTIVE",
        )
