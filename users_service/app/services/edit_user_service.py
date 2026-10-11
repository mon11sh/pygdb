"""
Edit User Service - Business logic for editing users.
"""

import logging
from typing import Optional
from ..models.request_models import EditUserRequest
from ..models.response_models import EditUserResponse
from ..repositories.user_repository import UserRepository
from ..services.audit_service import AuditService
from ..exceptions.user_management_exception import (
    UserNotFoundException,
    InvalidUserInputException,
    InvalidRoleException,
)
from ..utils.role_validator import RoleValidator
from ..utils.user_input_validator import UserInputValidator

logger = logging.getLogger(__name__)


class EditUserService:
    """Service for editing users."""
    
    def __init__(self, repo: UserRepository):
        """Initialize service with repository."""
        self.repo = repo
        self.validator = UserInputValidator()
        self.role_validator = RoleValidator()
    
    async def edit_user(self, login_id: str, request: EditUserRequest, performed_by: Optional[str] = None) -> EditUserResponse:
        """Edit an existing user."""
        logger.info(f"➡️ Editing user: {login_id}")

        # Get existing user
        user = await self.repo.get_user_by_login_id(login_id)
        if not user:
            raise UserNotFoundException(login_id)

        # Validate inputs
        self.validator.validate_edit_user_input(
            request.username,
            request.password,
            request.role
        )

        # F12a: Role is NOT editable via this endpoint. Per the documented
        # contract only username/password may change here. Any role supplied in
        # the request is deliberately ignored to prevent privilege escalation.
        # Role changes must go through a dedicated, explicitly-authorized flow.

        # Update user (role intentionally omitted so it stays unchanged)
        updated_user = await self.repo.update_user(
            user["user_id"],
            username=request.username,
            password=request.password
        )

        # Log audit action
        await AuditService.log_action(
            user_id=user["user_id"],
            action="UPDATE",
            old_data={
                "username": user["username"],
                "role": user["role"]
            },
            new_data={
                "username": updated_user["username"],
                "role": updated_user["role"]
            },
            performed_by=performed_by
        )
        
        logger.info(f"✅ User edited successfully: {login_id}")
        
        return EditUserResponse(
            user_id=updated_user["user_id"],
            username=updated_user["username"],
            login_id=updated_user["login_id"],
            role=updated_user["role"],
            created_at=updated_user["created_at"],
            is_active=updated_user["is_active"],
            message="User updated successfully"
        )
