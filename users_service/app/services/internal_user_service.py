"""Internal User Service - service-to-service user operations.

Provides credential verification and user status/role lookups consumed by other
internal microservices (e.g. authentication). Passwords are checked against
bcrypt hashes, and results are returned as plain dictionaries suitable for
internal API responses.
"""

import logging
import bcrypt
from typing import List, Optional

from ..repositories.user_repository import UserRepository

class InternalUserService:
    """Service class for internal user operations."""
    
    def __init__(self, repo: UserRepository):
        """
        Initialize service with repository.
        
        Args:
            repo: UserRepository instance
        """
        self.repo = repo
        self.logger = logging.getLogger(__name__)
    
    async def verify_user_credentials(self, login_id: str, password: str) -> dict:
        """
        Verify user credentials (login_id + password).
        
        Args:
            login_id: User's login identifier
            password: User's plaintext password
        
        Returns:
            Dictionary with:
            - is_valid: bool - Whether credentials are correct
            - user_id: int - User ID (if valid)
            - role: str - User role (if valid)
            - is_active: bool - User active status
        
        Raises:
            UserNotFoundException: If user doesn't exist
        """
        try:
            user = await self.repo.get_user_by_login_id(login_id)
            
            if not user:
                return {
                    "is_valid": False,
                    "user_id": None,
                    "role": None,
                    "is_active": False
                }
            
            # Verify password
            is_password_valid = await self._verify_password(password, user.get("password"))
            
            # Always return actual is_active status from database, regardless of password
            is_active_value = user.get("is_active", False)

            # F12d: We intentionally return the real is_active even when the
            # password is wrong so that dependent services (e.g. auth) can
            # distinguish "wrong password" from "inactive account". This is a
            # minor account-enumeration tradeoff (a caller can learn whether a
            # login_id exists / is active without valid credentials) accepted
            # here to preserve the internal contract other services rely on.
            return {
                "is_valid": is_password_valid,
                "user_id": user.get("user_id") if is_password_valid else None,
                "role": user.get("role") if is_password_valid else None,
                "is_active": is_active_value  # Always return actual status, not conditional on password
            }
        
        except Exception as e:
            self.logger.error(f"Error verifying credentials for {login_id}: {str(e)}")
            raise
    
    async def get_user_status(self, login_id: str) -> Optional[dict]:
        """
        Get user status and role by login_id.
        
        Args:
            login_id: User's login identifier
        
        Returns:
            Dictionary with:
            - user_id: int
            - login_id: str
            - is_active: bool
            - role: str
        
        Returns None if user doesn't exist.
        """
        try:
            user = await self.repo.get_user_by_login_id(login_id)
            
            if not user:
                return None
            
            return {
                "user_id": user.get("user_id"),
                "login_id": user.get("login_id"),
                "is_active": user.get("is_active", False),
                "role": user.get("role")
            }
        
        except Exception as e:
            self.logger.error(f"Error getting user status for {login_id}: {str(e)}")
            raise
    
    async def get_user_role(self, login_id: str) -> Optional[dict]:
        """
        Get user role by login_id.
        
        Args:
            login_id: User's login identifier
        
        Returns:
            Dictionary with:
            - user_id: int
            - login_id: str
            - role: str
        
        Returns None if user doesn't exist.
        """
        try:
            user = await self.repo.get_user_by_login_id(login_id)
            
            if not user:
                return None
            
            return {
                "user_id": user.get("user_id"),
                "login_id": user.get("login_id"),
                "role": user.get("role")
            }
        
        except Exception as e:
            self.logger.error(f"Error getting user role for {login_id}: {str(e)}")
            raise
    
    async def validate_user_role(self, login_id: str, required_role: str) -> Optional[dict]:
        """
        Validate if user has required role.
        
        Args:
            login_id: User's login identifier
            required_role: Role to validate against
        
        Returns:
            Dictionary with:
            - has_role: bool - Whether user has required role
            - user_role: str - User's actual role
            - is_active: bool - User active status
        
        Returns None if user doesn't exist.
        """
        try:
            user = await self.repo.get_user_by_login_id(login_id)
            
            if not user:
                return None
            
            user_role = user.get("role")
            has_role = user_role == required_role
            
            return {
                "has_role": has_role,
                "user_role": user_role,
                "is_active": user.get("is_active", False)
            }
        
        except Exception as e:
            self.logger.error(f"Error validating role for {login_id}: {str(e)}")
            raise
    
    async def bulk_validate_users(self, login_ids: List[str]) -> dict:
        """
        Bulk validate multiple users.
        
        Args:
            login_ids: List of login IDs to validate
        
        Returns:
            Dictionary with:
            - valid_users: List[dict] - Valid users found
            - invalid_users: List[str] - Login IDs not found
            - total_valid: int - Count of valid users
            - total_invalid: int - Count of invalid users
        """
        try:
            valid_users = []
            invalid_users = []
            
            for login_id in login_ids:
                user = await self.repo.get_user_by_login_id(login_id)
                
                if user:
                    valid_users.append({
                        "user_id": user.get("user_id"),
                        "login_id": user.get("login_id"),
                        "role": user.get("role"),
                        "is_active": user.get("is_active", False)
                    })
                else:
                    invalid_users.append(login_id)
            
            return {
                "valid_users": valid_users,
                "invalid_users": invalid_users,
                "total_valid": len(valid_users),
                "total_invalid": len(invalid_users)
            }
        
        except Exception as e:
            self.logger.error(f"Error in bulk validate: {str(e)}")
            raise
    
    @staticmethod
    async def _verify_password(plaintext: str, hashed: str) -> bool:
        """
        Verify plaintext password against bcrypt hash.
        
        Args:
            plaintext: Plaintext password
            hashed: Hashed password from database
        
        Returns:
            True if password matches, False otherwise
        """
        try:
            # bcrypt.checkpw expects bytes for both arguments
            # hashed password from DB is typically a string
            if isinstance(hashed, str):
                hashed = hashed.encode("utf-8")
            return bcrypt.checkpw(plaintext.encode("utf-8"), hashed)
        except Exception:
            return False
