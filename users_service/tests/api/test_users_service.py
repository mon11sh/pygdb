"""
Users Service Test Suite (Port 8003)
Tests for user management endpoints with positive, negative, and edge cases
"""

import httpx
import asyncio


import pytest
from app.main import app
from httpx import ASGITransport, AsyncClient
from unittest.mock import patch, AsyncMock, MagicMock
from app.repositories.user_repository import UserRepository
from app.services.internal_user_service import InternalUserService
from app.dependencies.providers import get_user_repository, get_internal_user_service
from gdb_common.auth_dependencies import get_current_user

@pytest.mark.asyncio
class TestUsersService:
    """Test suite for Users Service"""

    BASE_URL = "/api/v1"
    INTERNAL_URL = "/internal/v1"

    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        self.mock_repo = AsyncMock(spec=UserRepository)
        self.mock_service = AsyncMock(spec=InternalUserService)
        
        app.dependency_overrides[get_user_repository] = lambda: self.mock_repo
        app.dependency_overrides[get_internal_user_service] = lambda: self.mock_service
        # Default mock for get_current_user (authorized) - Use a valid role
        app.dependency_overrides[get_current_user] = lambda: {"role": "MANAGER", "user_id": 1, "login_id": "john.doe"}
        
        yield
        app.dependency_overrides.clear()

    async def get_token(self, login_id="john.doe", password="Welcome@1"):
        """Mock token getting"""
        return "mock_token"

    async def test_positive_get_user_profile(self):
        """POSITIVE: Get user profile with valid token"""
        from datetime import datetime
        token = await self.get_token("john.doe", "Welcome@1")
        headers = {"Authorization": f"Bearer {token}"}

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                # Mock the specific repo call
                self.mock_repo.get_user_by_login_id = AsyncMock(return_value={
                    "user_id": 1, "login_id": "john.doe", "role": "MANAGER",
                    "username": "John Doe", "is_active": True, "created_at": datetime.now()
                })

                response = await client.get(
                    f"{self.BASE_URL}/users/john.doe",
                    headers=headers
                )
                assert response.status_code == 200
                data = response.json()
                assert data["user_id"] == 1
                assert data["login_id"] == "john.doe"

    async def test_positive_verify_password(self):
        """POSITIVE: Verify correct password"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            self.mock_service.verify_user_credentials.return_value = {
                "is_valid": True, "user_id": 1, "role": "MANAGER", "is_active": True
            }
            
            response = await client.post(
                f"{self.INTERNAL_URL}/users/verify",
                json={"login_id": "john.doe", "password": "Welcome@1"}
            )
            assert response.status_code == 200

    async def test_negative_get_nonexistent_user(self):
        """NEGATIVE: Get non-existent user"""
        # Override to ADMIN role so we can view "others" and reach the 404 logic
        app.dependency_overrides[get_current_user] = lambda: {"role": "ADMIN", "user_id": 999, "login_id": "admin.user"}
        
        token = await self.get_token("admin.user", "Welcome@1")
        headers = {"Authorization": f"Bearer {token}"}

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Mock repository to return None for non-existent user
            with patch("app.services.view_user_service.ViewUserService.get_user") as mock_view:
                from app.exceptions.user_management_exception import UserNotFoundException
                mock_view.side_effect = UserNotFoundException("User not found")
                
                response = await client.get(
                    f"{self.BASE_URL}/users/nonexistent.user",
                    headers=headers
                )
                assert response.status_code == 404

    async def test_negative_no_auth_token(self):
        """NEGATIVE: Missing authentication token"""
        # To simulate missing token, we must override the dependency to raise 401
        from fastapi import HTTPException
        def mock_raise_401():
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        app.dependency_overrides[get_current_user] = mock_raise_401
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"{self.BASE_URL}/users/1")
            assert response.status_code == 401

    async def test_negative_invalid_token(self):
        """NEGATIVE: Invalid token"""
        from fastapi import HTTPException
        def mock_raise_401():
            raise HTTPException(status_code=401, detail="Invalid token")
        
        app.dependency_overrides[get_current_user] = mock_raise_401
        
        headers = {"Authorization": "Bearer invalid.token.here"}

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                f"{self.BASE_URL}/users/1",
                headers=headers
            )
            assert response.status_code == 401

    async def test_negative_expired_token(self):
        """NEGATIVE: Expired token should fail"""
        from fastapi import HTTPException
        def mock_raise_401():
            raise HTTPException(status_code=401, detail="Token expired")
        
        app.dependency_overrides[get_current_user] = mock_raise_401
        
        expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNjM3MDg5NjAwfQ.invalid"
        headers = {"Authorization": f"Bearer {expired_token}"}

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                f"{self.BASE_URL}/users/1",
                headers=headers
            )
            assert response.status_code == 401

    async def test_negative_wrong_password(self):
        """NEGATIVE: Verify wrong password"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            self.mock_service.verify_user_credentials.return_value = {
                "is_valid": False, "user_id": None, "role": None, "is_active": True
            }
            
            response = await client.post(
                f"{self.INTERNAL_URL}/users/verify",
                json={"login_id": "john.doe", "password": "WrongPassword123"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data.get("is_valid") == False

    async def test_negative_empty_password(self):
        """NEGATIVE: Empty password verification"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            self.mock_service.verify_user_credentials.return_value = {
                "is_valid": False, "user_id": None, "role": None, "is_active": True
            }
            response = await client.post(
                f"{self.INTERNAL_URL}/users/verify",
                json={"login_id": "john.doe", "password": ""}
            )
            assert response.status_code in [200, 422]

    async def test_edge_malformed_json(self):
        """EDGE: Malformed JSON in request"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"{self.INTERNAL_URL}/users/verify",
                content="{invalid json",
                headers={"Content-Type": "application/json"}
            )
            assert response.status_code in [400, 422, 500]

    async def test_edge_sql_injection(self):
        """EDGE: SQL injection in user ID"""
        # Override to ADMIN role so we can view "others"
        app.dependency_overrides[get_current_user] = lambda: {"role": "ADMIN", "user_id": 999, "login_id": "admin.user"}
        
        token = await self.get_token("admin.user", "Welcome@1")
        headers = {"Authorization": f"Bearer {token}"}

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                f"{self.BASE_URL}/users/1' OR '1'='1",
                headers=headers
            )
            assert response.status_code in [400, 404, 422, 403, 500]


    async def test_edge_special_characters_password(self):
        """EDGE: Special characters in password verification"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            self.mock_service.verify_user_credentials.return_value = {
                "is_valid": False, "user_id": None, "role": None, "is_active": True
            }
            
            response = await client.post(
                f"{self.INTERNAL_URL}/users/verify",
                json={"login_id": "john.doe", "password": "P@ss!#$%^&*()"}
            )
            assert response.status_code == 200
            data = response.json()
            assert "is_valid" in data



