"""
User Input Validator - Validates user input for operations.
"""

import logging
import re
from typing import Optional
from ..exceptions.user_management_exception import InvalidUserInputException

logger = logging.getLogger(__name__)


class UserInputValidator:
    """Validator for user input."""
    
    @staticmethod
    def validate_add_user_input(username: str, login_id: str, password: str, role: Optional[str] = None):
        """Validate inputs for adding a user."""
        if not username or len(username) < 1 or len(username) > 255:
            raise InvalidUserInputException("username", "must be between 1 and 255 characters")
        
        logger.info(f"✅ Username validated: {username}")
        
        if not login_id or len(login_id) < 3 or len(login_id) > 50:
            raise InvalidUserInputException("login_id", "must be between 3 and 50 characters")
        
        if not re.match(r"^[a-zA-Z0-9._-]+$", login_id):
            raise InvalidUserInputException("login_id", "can only contain alphanumeric, dots, hyphens, underscores")
        
        logger.info(f"✅ login_id validated: {login_id}")
        
        if not password or len(password) < 8:
            raise InvalidUserInputException("password", "must be at least 8 characters")
        
        if not any(char.isupper() for char in password):
            raise InvalidUserInputException("password", "must contain at least one uppercase letter")
        
        if not any(char.isdigit() for char in password):
            raise InvalidUserInputException("password", "must contain at least one digit")
        
        logger.info(f"✅ Password validated")
        logger.info(f"✅ All user creation inputs validated")
    
    @staticmethod
    def validate_edit_user_input(username: Optional[str] = None, password: Optional[str] = None, role: Optional[str] = None):
        """Validate inputs for editing a user."""
        if username is not None:
            if len(username) < 1 or len(username) > 255:
                raise InvalidUserInputException("username", "must be between 1 and 255 characters")
        
        if password is not None:
            if len(password) < 8:
                raise InvalidUserInputException("password", "must be at least 8 characters")
            if not any(char.isupper() for char in password):
                raise InvalidUserInputException("password", "must contain at least one uppercase letter")
            if not any(char.isdigit() for char in password):
                raise InvalidUserInputException("password", "must contain at least one digit")
        
        logger.info(f"✅ Edit user inputs validated")
