"""Last-active-admin exception for the user management service.

Defines ``LastAdminException``, raised to prevent inactivating a user when doing
so would leave the system with no active ADMIN, returning an HTTP 400 error.
"""

from .user_management_exception_base import UserManagementException

class LastAdminException(UserManagementException):
    """Raised when inactivating a user would leave zero active ADMINs."""

    def __init__(self, login_id: str):
        """Initialize LastAdminException."""
        super().__init__(
            status_code=400,
            detail=(
                f"Cannot inactivate user '{login_id}': at least one active "
                f"ADMIN must remain in the system"
            ),
            error_code="LAST_ACTIVE_ADMIN",
        )
