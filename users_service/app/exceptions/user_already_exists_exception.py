"""User-already-exists exception for the user management service.

Defines ``UserAlreadyExistsException``, raised when creating a user whose
``login_id`` is already taken, returning an HTTP 409 conflict error.
"""

from .user_management_exception_base import UserManagementException

class UserAlreadyExistsException(UserManagementException):
    """Raised when attempting to create a user with existing login_id."""

    def __init__(self, login_id: str):
        """Initialize UserAlreadyExistsException."""
        super().__init__(
            status_code=409,
            detail=f"User with login_id '{login_id}' already exists",
            error_code="USER_ALREADY_EXISTS",
        )
