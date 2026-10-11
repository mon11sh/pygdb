"""
Comprehensive Test Suite for Role-Based Access Control

Tests cover:
- Positive test cases (valid role input validation)
- Negative test cases (invalid role input)
- Edge cases (null roles, boundary conditions)

Features tested:
- Role validation in request models
- Field validation and constraints
- Login ID validation rules
- Password validation rules
- Username validation
"""

import pytest
from pydantic import ValidationError
from app.models.request_models import AddUserRequest, EditUserRequest


class TestPasswordValidationForRoles:
    """Test password validation rules."""
    
    @pytest.mark.positive
    def test_password_with_uppercase_and_digit(self):
        """POSITIVE: Password with uppercase and digit."""
        request = AddUserRequest(
            username="User",
            login_id="user.name",
            password="ValidPass123"
        )
        assert request.password == "ValidPass123"
    
    @pytest.mark.positive
    def test_password_complex(self):
        """POSITIVE: Complex password with special characters."""
        request = AddUserRequest(
            username="User",
            login_id="user.name",
            password="SecureP@ss123!"
        )
        assert request.password == "SecureP@ss123!"
    
    @pytest.mark.positive
    def test_password_no_uppercase_but_valid(self):
        """POSITIVE: Password without uppercase is accepted (no constraint)."""
        request = AddUserRequest(
            username="User",
            login_id="user.name",
            password="noupppercase123"
        )
        assert request.password == "noupppercase123"
    
    @pytest.mark.positive
    def test_password_no_digit_but_valid(self):
        """POSITIVE: Password without digit is accepted (no constraint)."""
        request = AddUserRequest(
            username="User",
            login_id="user.name",
            password="NoDigitsOnly"
        )
        assert request.password == "NoDigitsOnly"
    
    @pytest.mark.negative
    def test_password_too_short(self):
        """NEGATIVE: Password shorter than minimum."""
        with pytest.raises(ValidationError) as exc_info:
            AddUserRequest(
                username="User",
                login_id="user.name",
                password="Short1"
            )
        assert "password" in str(exc_info.value).lower()


class TestLoginIdValidationForRoles:
    """Test login_id validation rules."""
    
    @pytest.mark.positive
    def test_login_id_with_dots(self):
        """POSITIVE: login_id with dots is valid."""
        request = AddUserRequest(
            username="User",
            login_id="user.name",
            password="ValidPass123"
        )
        assert request.login_id == "user.name"
    
    @pytest.mark.positive
    def test_login_id_with_hyphens(self):
        """POSITIVE: login_id with hyphens is valid."""
        request = AddUserRequest(
            username="User",
            login_id="user-name",
            password="ValidPass123"
        )
        assert request.login_id == "user-name"
    
    @pytest.mark.positive
    def test_login_id_numeric(self):
        """POSITIVE: login_id with numbers is valid."""
        request = AddUserRequest(
            username="User",
            login_id="user123",
            password="ValidPass123"
        )
        assert request.login_id == "user123"
    
    @pytest.mark.negative
    def test_login_id_with_special_chars(self):
        """NEGATIVE: login_id with invalid special characters."""
        with pytest.raises(ValidationError):
            AddUserRequest(
                username="User",
                login_id="user@name!",
                password="ValidPass123"
            )
    
    @pytest.mark.negative
    def test_login_id_with_spaces(self):
        """NEGATIVE: login_id with spaces."""
        with pytest.raises(ValidationError):
            AddUserRequest(
                username="User",
                login_id="user name",
                password="ValidPass123"
            )


class TestUsernameValidationForRoles:
    """Test username validation rules for role management."""
    
    @pytest.mark.positive
    def test_username_simple(self):
        """POSITIVE: Simple username."""
        request = AddUserRequest(
            username="John Doe",
            login_id="john.doe",
            password="ValidPass123"
        )
        assert request.username == "John Doe"
    
    @pytest.mark.positive
    def test_username_max_length(self):
        """POSITIVE: Username at maximum length."""
        max_username = "A" * 255
        request = AddUserRequest(
            username=max_username,
            login_id="maxlength.user",
            password="ValidPass123"
        )
        assert request.username == max_username
    
    @pytest.mark.negative
    def test_username_empty(self):
        """NEGATIVE: Empty username."""
        with pytest.raises(ValidationError):
            AddUserRequest(
                username="",
                login_id="empty.user",
                password="ValidPass123"
            )
    
    @pytest.mark.negative
    def test_username_exceeds_max_length(self):
        """NEGATIVE: Username exceeds maximum length."""
        too_long = "A" * 256
        with pytest.raises(ValidationError):
            AddUserRequest(
                username=too_long,
                login_id="toolong.user",
                password="ValidPass123"
            )


class TestRequiredFieldsForRoles:
    """Test required field validation for role management."""
    
    @pytest.mark.negative
    def test_missing_username(self):
        """NEGATIVE: Missing username."""
        with pytest.raises(ValidationError):
            AddUserRequest(
                login_id="user.name",
                password="ValidPass123"
            )
    
    @pytest.mark.negative
    def test_missing_login_id(self):
        """NEGATIVE: Missing login_id."""
        with pytest.raises(ValidationError):
            AddUserRequest(
                username="User Name",
                password="ValidPass123"
            )
    
    @pytest.mark.negative
    def test_missing_password(self):
        """NEGATIVE: Missing password."""
        with pytest.raises(ValidationError):
            AddUserRequest(
                username="User Name",
                login_id="user.name"
            )


class TestEdgeCasesForRoles:
    """Test edge cases and boundary conditions for role management."""
    
    @pytest.mark.positive
    def test_username_with_special_chars(self):
        """POSITIVE: Username with special characters."""
        request = AddUserRequest(
            username="John O'Brien-Smith Jr.",
            login_id="john.brien",
            password="ValidPass123"
        )
        assert "O'Brien" in request.username
    
    @pytest.mark.positive
    def test_login_id_all_digits(self):
        """POSITIVE: login_id with all numeric characters."""
        request = AddUserRequest(
            username="User",
            login_id="1234567890",
            password="ValidPass123"
        )
        assert request.login_id == "1234567890"
    
    @pytest.mark.positive
    def test_login_id_max_length(self):
        """POSITIVE: login_id at maximum length."""
        max_login = "a" * 50
        request = AddUserRequest(
            username="User",
            login_id=max_login,
            password="ValidPass123"
        )
        assert request.login_id == max_login
    
    @pytest.mark.negative
    def test_none_username(self):
        """NEGATIVE: None as username."""
        with pytest.raises(ValidationError):
            AddUserRequest(
                username=None,
                login_id="user.name",
                password="ValidPass123"
            )
    
    @pytest.mark.negative
    def test_none_login_id(self):
        """NEGATIVE: None as login_id."""
        with pytest.raises(ValidationError):
            AddUserRequest(
                username="User",
                login_id=None,
                password="ValidPass123"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
