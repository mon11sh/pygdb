"""User-already-inactive exception for the user management service.

Defines ``UserAlreadyInactiveException``, raised when an inactivation is
requested for a user that is already inactive, returning an HTTP 400 error.
"""

from .user_management_exception_base import UserManagementException

class UserAlreadyInactiveException(UserManagementException):
    """Raised when attempting to inactivate an already inactive user."""

    def __init__(self, login_id: str):
        """Initialize UserAlreadyInactiveException."""
        super().__init__(
            status_code=400,
            detail=f"User with login_id '{login_id}' is already inactive",
            error_code="USER_ALREADY_INACTIVE",
        )
