"""Convenience re-export module for user management exceptions.

Collects the individual exception classes from their respective modules into a
single import surface, allowing callers to import any user management exception
from one location.
"""

from .user_management_exception_base import UserManagementException
from .user_already_exists_exception import UserAlreadyExistsException
from .user_not_found_exception import UserNotFoundException
from .user_inactive_exception import UserInactiveException
from .user_already_inactive_exception import UserAlreadyInactiveException
from .invalid_user_input_exception import InvalidUserInputException
from .database_exception import DatabaseException
from .invalid_role_exception import InvalidRoleException
from .user_already_active_exception import UserAlreadyActiveException
from .last_admin_exception import LastAdminException
