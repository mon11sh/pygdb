"""
Activate User Service - Business logic for activating users.
"""

import logging
from typing import Optional
from ..models.response_models import InactivateUserResponse
from ..repositories.user_repository import UserRepository
from ..services.audit_service import AuditService
from ..exceptions.user_management_exception import (
    UserNotFoundException,
    UserAlreadyActiveException,
)

logger = logging.getLogger(__name__)


class ActivateUserService:
    """Service for activating users."""
    
    def __init__(self, repo: UserRepository):
        """Initialize service with repository."""
        self.repo = repo
    
    async def activate_user(self, login_id: str, performed_by: Optional[str] = None) -> InactivateUserResponse:
        """Activate a user."""
        logger.info(f"➡️ Activating user: {login_id}")
        
        # Get user
        user = await self.repo.get_user_by_login_id(login_id)
        if not user:
            raise UserNotFoundException(login_id)
        
        # Check if already active
        if user["is_active"]:
            raise UserAlreadyActiveException(login_id)
        
        # Activate user
        updated_user = await self.repo.activate_user(user["user_id"])
        
        # Log audit action
        await AuditService.log_action(
            user_id=user["user_id"],
            action="REACTIVATE",
            old_data={"is_active": user["is_active"]},
            new_data={"is_active": updated_user["is_active"]},
            performed_by=performed_by
        )
        
        logger.info(f"✅ User activated successfully: {login_id}")
        
        return InactivateUserResponse(
            user_id=updated_user["user_id"],
            username=updated_user["username"],
            login_id=updated_user["login_id"],
            role=updated_user["role"],
            created_at=updated_user["created_at"],
            is_active=updated_user["is_active"],
            message="User activated successfully"
        )
