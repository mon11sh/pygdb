"""
View User Service - Business logic for viewing users.
"""

import logging
from typing import List
from ..models.response_models import ViewUserResponse, ListUsersResponse
from ..repositories.user_repository import UserRepository
from ..exceptions.user_management_exception import UserNotFoundException

logger = logging.getLogger(__name__)


class ViewUserService:
    """Service for viewing users."""
    
    def __init__(self, repo: UserRepository):
        """Initialize service with repository."""
        self.repo = repo
    
    async def get_user(self, login_id: str) -> ViewUserResponse:
        """Get a single user by login_id."""
        logger.info(f"➡️ Fetching user: {login_id}")
        
        user = await self.repo.get_user_by_login_id(login_id)
        if not user:
            raise UserNotFoundException(login_id)
        
        logger.info(f"✅ User fetched: {login_id}")
        
        return ViewUserResponse(
            user_id=user["user_id"],
            username=user["username"],
            login_id=user["login_id"],
            role=user["role"],
            created_at=user["created_at"],
            is_active=user["is_active"]
        )
    
    async def list_users(self) -> ListUsersResponse:
        """List all users."""
        logger.info("➡️ Fetching all users")
        
        users_data = await self.repo.get_all_users()
        
        users = [
            ViewUserResponse(
                user_id=user["user_id"],
                username=user["username"],
                login_id=user["login_id"],
                role=user["role"],
                created_at=user["created_at"],
                is_active=user["is_active"]
            )
            for user in users_data
        ]
        
        logger.info(f"✅ Fetched {len(users)} users")
        
        return ListUsersResponse(
            users=users,
            total_count=len(users)
        )
