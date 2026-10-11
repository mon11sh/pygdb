"""
Add User Service - Business logic for adding new users.
"""

import logging
from typing import Optional
from ..models.request_models import AddUserRequest
from ..models.response_models import AddUserResponse
from ..repositories.user_repository import UserRepository
from ..services.audit_service import AuditService
from ..exceptions.user_management_exception import (
    UserAlreadyExistsException,
    InvalidUserInputException,
    InvalidRoleException,
)
from ..utils.role_validator import RoleValidator
from ..utils.user_input_validator import UserInputValidator

logger = logging.getLogger(__name__)


class AddUserService:
    """Service for adding new users."""
    
    def __init__(self, repo: UserRepository):
        """Initialize service with repository."""
        self.repo = repo
        self.validator = UserInputValidator()
        self.role_validator = RoleValidator()
    
    async def add_user(self, request: AddUserRequest, performed_by: Optional[str] = None) -> AddUserResponse:
        """
        Add a new user.

        Args:
            request: User creation request
            performed_by: login_id of the admin performing this action (for audit)

        Returns:
            AddUserResponse: Response with created user details
            
        Raises:
            UserAlreadyExistsException: If user already exists
            InvalidUserInputException: If input is invalid
            InvalidRoleException: If role is invalid
        """
        logger.info(f"➡️ Starting add user for: {request.login_id}")
        
        # Validate inputs
        self.validator.validate_add_user_input(
            request.username, 
            request.login_id, 
            request.password,
            request.role
        )
        
        # Validate role
        role = self.role_validator.validate_role(request.role)
        
        # Check if user already exists
        existing_user = await self.repo.get_user_by_login_id(request.login_id)
        if existing_user:
            raise UserAlreadyExistsException(request.login_id)
        
        # Create user
        user = await self.repo.create_user(
            username=request.username,
            login_id=request.login_id,
            password=request.password,
            role=role
        )
        
        # Log audit action
        await AuditService.log_action(
            user_id=user["user_id"],
            action="CREATE",
            new_data={
                "username": user["username"],
                "login_id": user["login_id"],
                "role": user["role"],
                "is_active": user["is_active"]
            },
            performed_by=performed_by
        )
        
        logger.info(f"✅ User created successfully: {request.login_id} with role: {role}")
        
        return AddUserResponse(
            user_id=user["user_id"],
            username=user["username"],
            login_id=user["login_id"],
            role=user["role"],
            created_at=user["created_at"],
            is_active=user["is_active"],
            message="User created successfully"
        )
