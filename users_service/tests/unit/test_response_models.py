"""Comprehensive tests for response models."""

import pytest
from datetime import datetime
from pydantic import ValidationError
from app.models.response_models import (
    UserResponse,
    AddUserResponse,
    EditUserResponse,
    ViewUserResponse,
    ListUsersResponse,
    InactivateUserResponse,
    ErrorResponse,
)


class TestUserResponse:
    """Tests for UserResponse model."""

    @pytest.mark.positive
    def test_valid_user_response(self):
        """Test creating a valid UserResponse."""
        now = datetime.now()
        response = UserResponse(
            user_id=1,
            username="John Doe",
            login_id="john.doe",
            created_at=now,
            is_active=True,
        )
        assert response.user_id == 1
        assert response.username == "John Doe"
        assert response.login_id == "john.doe"
        assert response.is_active is True

    @pytest.mark.positive
    def test_user_response_with_inactive_user(self):
        """Test UserResponse with inactive user."""
        response = UserResponse(
            user_id=2,
            username="Jane Doe",
            login_id="jane.doe",
            created_at=datetime.now(),
            is_active=False,
        )
        assert response.is_active is False

    @pytest.mark.positive
    def test_user_response_json_serialization(self):
        """Test UserResponse JSON serialization."""
        from pydantic import TypeAdapter
        now = datetime.now()
        response = UserResponse(
            user_id=1,
            username="John Doe",
            login_id="john.doe",
            created_at=now,
            is_active=True,
        )
        json_data = TypeAdapter(UserResponse).dump_json(response).decode()
        assert "john.doe" in json_data
        assert "John Doe" in json_data

    @pytest.mark.positive
    def test_user_response_from_attributes(self):
        """Test UserResponse using from_attributes."""
        user_dict = {
            "user_id": 1,
            "username": "John Doe",
            "login_id": "john.doe",
            "created_at": datetime.now(),
            "is_active": True,
        }
        response = UserResponse(**user_dict)
        assert response.user_id == 1

    @pytest.mark.negative
    def test_user_response_missing_user_id(self):
        """Test UserResponse missing user_id."""
        with pytest.raises(ValidationError):
            UserResponse(
                username="John Doe",
                login_id="john.doe",
                created_at=datetime.now(),
                is_active=True,
            )

    @pytest.mark.negative
    def test_user_response_missing_username(self):
        """Test UserResponse missing username."""
        with pytest.raises(ValidationError):
            UserResponse(
                user_id=1,
                login_id="john.doe",
                created_at=datetime.now(),
                is_active=True,
            )

    @pytest.mark.negative
    def test_user_response_missing_login_id(self):
        """Test UserResponse missing login_id."""
        with pytest.raises(ValidationError):
            UserResponse(
                user_id=1,
                username="John Doe",
                created_at=datetime.now(),
                is_active=True,
            )

    @pytest.mark.negative
    def test_user_response_missing_created_at(self):
        """Test UserResponse missing created_at."""
        with pytest.raises(ValidationError):
            UserResponse(
                user_id=1,
                username="John Doe",
                login_id="john.doe",
                is_active=True,
            )

    @pytest.mark.negative
    def test_user_response_missing_is_active(self):
        """Test UserResponse missing is_active."""
        with pytest.raises(ValidationError):
            UserResponse(
                user_id=1,
                username="John Doe",
                login_id="john.doe",
                created_at=datetime.now(),
            )

    @pytest.mark.negative
    def test_user_response_with_invalid_user_id_type(self):
        """Test UserResponse with invalid user_id type."""
        with pytest.raises(ValidationError):
            UserResponse(
                user_id="invalid",
                username="John Doe",
                login_id="john.doe",
                created_at=datetime.now(),
                is_active=True,
            )

    @pytest.mark.negative
    def test_user_response_with_invalid_is_active_type(self):
        """Test UserResponse with string boolean is coerced by Pydantic v2."""
        # Pydantic v2 coerces string "true" to boolean True
        response = UserResponse(
            user_id=1,
            username="John Doe",
            login_id="john.doe",
            created_at=datetime.now(),
            is_active="true",
        )
        assert response.is_active is True

    @pytest.mark.edge_case
    def test_user_response_with_large_user_id(self):
        """Test UserResponse with very large user_id."""
        response = UserResponse(
            user_id=999999999,
            username="John Doe",
            login_id="john.doe",
            created_at=datetime.now(),
            is_active=True,
        )
        assert response.user_id == 999999999


class TestAddUserResponse:
    """Tests for AddUserResponse model."""

    @pytest.mark.positive
    def test_valid_add_user_response(self):
        """Test creating a valid AddUserResponse."""
        now = datetime.now()
        response = AddUserResponse(
            user_id=1,
            username="John Doe",
            login_id="john.doe",
            created_at=now,
            is_active=True,
            message="User created successfully",
        )
        assert response.user_id == 1
        assert response.message == "User created successfully"

    @pytest.mark.positive
    def test_add_user_response_with_default_message(self):
        """Test AddUserResponse with default message."""
        response = AddUserResponse(
            user_id=1,
            username="John Doe",
            login_id="john.doe",
            created_at=datetime.now(),
            is_active=True,
        )
        assert response.message == "User created successfully"

    @pytest.mark.positive
    def test_add_user_response_custom_message(self):
        """Test AddUserResponse with custom message."""
        response = AddUserResponse(
            user_id=1,
            username="John Doe",
            login_id="john.doe",
            created_at=datetime.now(),
            is_active=True,
            message="Custom message",
        )
        assert response.message == "Custom message"


class TestEditUserResponse:
    """Tests for EditUserResponse model."""

    @pytest.mark.positive
    def test_valid_edit_user_response(self):
        """Test creating a valid EditUserResponse."""
        response = EditUserResponse(
            user_id=1,
            username="Jane Doe",
            login_id="john.doe",
            created_at=datetime.now(),
            is_active=True,
            message="User updated successfully",
        )
        assert response.username == "Jane Doe"
        assert response.message == "User updated successfully"

    @pytest.mark.positive
    def test_edit_user_response_with_default_message(self):
        """Test EditUserResponse with default message."""
        response = EditUserResponse(
            user_id=1,
            username="Jane Doe",
            login_id="john.doe",
            created_at=datetime.now(),
            is_active=True,
        )
        assert response.message == "User updated successfully"


class TestViewUserResponse:
    """Tests for ViewUserResponse model."""

    @pytest.mark.positive
    def test_valid_view_user_response(self):
        """Test creating a valid ViewUserResponse."""
        response = ViewUserResponse(
            user_id=1,
            username="John Doe",
            login_id="john.doe",
            created_at=datetime.now(),
            is_active=True,
        )
        assert response.user_id == 1

    @pytest.mark.positive
    def test_view_user_response_matches_user_response(self):
        """Test ViewUserResponse inherits from UserResponse."""
        response = ViewUserResponse(
            user_id=1,
            username="John Doe",
            login_id="john.doe",
            created_at=datetime.now(),
            is_active=True,
        )
        assert isinstance(response, UserResponse)


class TestListUsersResponse:
    """Tests for ListUsersResponse model."""

    @pytest.mark.positive
    def test_valid_list_users_response(self):
        """Test creating a valid ListUsersResponse."""
        now = datetime.now()
        users = [
            UserResponse(
                user_id=1,
                username="John Doe",
                login_id="john.doe",
                created_at=now,
                is_active=True,
            ),
            UserResponse(
                user_id=2,
                username="Jane Doe",
                login_id="jane.doe",
                created_at=now,
                is_active=True,
            ),
        ]
        response = ListUsersResponse(users=users, total_count=2)
        assert len(response.users) == 2
        assert response.total_count == 2

    @pytest.mark.positive
    def test_list_users_response_with_empty_list(self):
        """Test ListUsersResponse with empty user list."""
        response = ListUsersResponse(users=[], total_count=0)
        assert len(response.users) == 0
        assert response.total_count == 0

    @pytest.mark.positive
    def test_list_users_response_with_many_users(self):
        """Test ListUsersResponse with many users."""
        now = datetime.now()
        users = [
            UserResponse(
                user_id=i,
                username=f"User {i}",
                login_id=f"user.{i}",
                created_at=now,
                is_active=True,
            )
            for i in range(100)
        ]
        response = ListUsersResponse(users=users, total_count=100)
        assert response.total_count == 100

    @pytest.mark.negative
    def test_list_users_response_missing_users(self):
        """Test ListUsersResponse missing users."""
        with pytest.raises(ValidationError):
            ListUsersResponse(total_count=0)

    @pytest.mark.negative
    def test_list_users_response_missing_total_count(self):
        """Test ListUsersResponse missing total_count."""
        with pytest.raises(ValidationError):
            ListUsersResponse(users=[])

    @pytest.mark.edge_case
    def test_list_users_response_mismatched_count(self):
        """Test ListUsersResponse with mismatched count."""
        now = datetime.now()
        users = [
            UserResponse(
                user_id=1,
                username="John Doe",
                login_id="john.doe",
                created_at=now,
                is_active=True,
            ),
        ]
        response = ListUsersResponse(users=users, total_count=5)
        assert len(response.users) == 1
        assert response.total_count == 5


class TestInactivateUserResponse:
    """Tests for InactivateUserResponse model."""

    @pytest.mark.positive
    def test_valid_inactivate_user_response(self):
        """Test creating a valid InactivateUserResponse."""
        response = InactivateUserResponse(
            user_id=1,
            username="John Doe",
            login_id="john.doe",
            created_at=datetime.now(),
            is_active=False,
            message="User inactivated successfully",
        )
        assert response.is_active is False
        assert response.message == "User inactivated successfully"

    @pytest.mark.positive
    def test_inactivate_user_response_with_default_message(self):
        """Test InactivateUserResponse with default message."""
        response = InactivateUserResponse(
            user_id=1,
            username="John Doe",
            login_id="john.doe",
            created_at=datetime.now(),
            is_active=False,
        )
        assert response.message == "User inactivated successfully"


class TestErrorResponse:
    """Tests for ErrorResponse model."""

    @pytest.mark.positive
    def test_valid_error_response(self):
        """Test creating a valid ErrorResponse."""
        response = ErrorResponse(
            error_code="USER_NOT_FOUND",
            detail="User with login_id 'invalid' not found",
        )
        assert response.error_code == "USER_NOT_FOUND"
        assert response.detail == "User with login_id 'invalid' not found"

    @pytest.mark.positive
    def test_error_response_with_long_detail(self):
        """Test ErrorResponse with long detail message."""
        detail = "A" * 500
        response = ErrorResponse(
            error_code="DATABASE_ERROR",
            detail=detail,
        )
        assert response.detail == detail

    @pytest.mark.negative
    def test_error_response_missing_error_code(self):
        """Test ErrorResponse missing error_code."""
        with pytest.raises(ValidationError):
            ErrorResponse(detail="Error detail")

    @pytest.mark.negative
    def test_error_response_missing_detail(self):
        """Test ErrorResponse missing detail."""
        with pytest.raises(ValidationError):
            ErrorResponse(error_code="ERROR")

    @pytest.mark.edge_case
    def test_error_response_all_error_codes(self):
        """Test ErrorResponse with all possible error codes."""
        error_codes = [
            "USER_ALREADY_EXISTS",
            "USER_NOT_FOUND",
            "USER_INACTIVE",
            "INVALID_INPUT",
            "DATABASE_ERROR",
            "INTERNAL_ERROR",
        ]
        for code in error_codes:
            response = ErrorResponse(error_code=code, detail="Test error")
            assert response.error_code == code
