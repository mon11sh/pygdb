"""
Role Validator - Validates and normalizes user roles.
"""

import logging
from typing import Optional
from ..exceptions.user_management_exception import InvalidRoleException

logger = logging.getLogger(__name__)

VALID_ROLES = ["MANAGER", "TELLER", "ADMIN"]


class RoleValidator:
    """Validator for user roles."""
    
    @staticmethod
    def validate_role(role: Optional[str] = None) -> str:
        """
        Validate and normalize role.
        
        Args:
            role: Role to validate (case-insensitive)
            
        Returns:
            str: Normalized role (uppercase)
            
        Raises:
            InvalidRoleException: If role is invalid
        """
        # Default to MANAGER if no role provided
        if role is None or role.strip() == "":
            logger.info("✅ Role validated: MANAGER (default)")
            return "MANAGER"
        
        # Normalize to uppercase and strip whitespace
        normalized_role = role.strip().upper()
        
        if normalized_role not in VALID_ROLES:
            raise InvalidRoleException(normalized_role, VALID_ROLES)
        
        logger.info(f"✅ Role validated: {normalized_role} ")
        return normalized_role
    
    @staticmethod
    def is_valid_role(role: str) -> bool:
        """
        Check if role is valid.
        
        Args:
            role: Role to check
            
        Returns:
            bool: True if valid, False otherwise
        """
        return role.strip().upper() in VALID_ROLES
    
    @staticmethod
    def get_valid_roles() -> list:
        """
        Get list of valid roles.
        
        Returns:
            list: List of valid roles
        """
        return VALID_ROLES
