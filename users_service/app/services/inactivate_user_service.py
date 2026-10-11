"""
Inactivate User Service - Business logic for inactivating users.
"""

import logging
from typing import Optional
from ..models.response_models import InactivateUserResponse
from ..repositories.user_repository import UserRepository
from ..services.audit_service import AuditService
from ..exceptions.user_management_exception import (
    UserNotFoundException,
    UserAlreadyInactiveException,
    LastAdminException,
)

logger = logging.getLogger(__name__)


class InactivateUserService:
    """Service for inactivating users."""
    
    def __init__(self, repo: UserRepository):
        """Initialize service with repository."""
        self.repo = repo
    
    async def inactivate_user(self, login_id: str, performed_by: Optional[str] = None) -> InactivateUserResponse:
        """Inactivate a user."""
        logger.info(f"➡️ Inactivating user: {login_id}")

        # Get user
        user = await self.repo.get_user_by_login_id(login_id)
        if not user:
            raise UserNotFoundException(login_id)

        # Check if already inactive
        if not user["is_active"]:
            raise UserAlreadyInactiveException(login_id)

        # F12b: Last-admin / self-lockout guard.
        # If the target is an active ADMIN and is the last remaining active
        # ADMIN, refuse the operation so the system can never be left with no
        # way to administer users. This also covers an admin inactivating
        # themselves as the final admin (self-lockout).
        if user["role"] == "ADMIN":
            active_admin_count = await self.repo.count_active_admins()
            if active_admin_count <= 1:
                logger.warning(
                    f"Blocked inactivation of last active admin: {login_id}"
                )
                raise LastAdminException(login_id)

        # Inactivate user
        updated_user = await self.repo.inactivate_user(user["user_id"])

        # Log audit action
        await AuditService.log_action(
            user_id=user["user_id"],
            action="INACTIVATE",
            old_data={"is_active": user["is_active"]},
            new_data={"is_active": updated_user["is_active"]},
            performed_by=performed_by
        )
        
        logger.info(f"✅ User inactivated successfully: {login_id}")
        
        return InactivateUserResponse(
            user_id=updated_user["user_id"],
            username=updated_user["username"],
            login_id=updated_user["login_id"],
            role=updated_user["role"],
            created_at=updated_user["created_at"],
            is_active=updated_user["is_active"],
            message="User inactivated successfully"
        )
