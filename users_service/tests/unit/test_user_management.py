"""
Comprehensive Test Suite for User Management

Tests cover:
- Positive test cases (valid requests)
- Negative test cases (invalid requests)
- Edge cases (boundary conditions)

Features tested:
- AddUserRequest model validation
- EditUserRequest model validation
- Field constraints and validation rules
- Required fields validation
"""

import pytest
from pydantic import ValidationError
from app.models.request_models import AddUserRequest, EditUserRequest


class TestAddUserRequestValidation:
    """Test AddUserRequest model validation."""
    
    @pytest.mark.positive
    def test_valid_add_user_request(self):
        """POSITIVE: Valid user creation request."""
        request = AddUserRequest(
            username="John Doe",
            login_id="john.doe",
            password="SecurePass123"
        )
        assert request.username == "John Doe"
        assert request.login_id == "john.doe"
        assert request.password == "SecurePass123"
    
    @pytest.mark.positive
    def test_add_user_with_all_fields(self):
        """POSITIVE: User request with all valid fields."""
        request = AddUserRequest(
            username="Jane Smith",
            login_id="jane.smith",
            password="StrongPass456"
        )
        assert request.username == "Jane Smith"
        assert request.login_id == "jane.smith"
        assert request.password == "StrongPass456"
    
    @pytest.mark.positive
    def test_valid_request_minimum_valid_password(self):
        """POSITIVE: Valid request with minimum acceptable password."""
        request = AddUserRequest(
            username="User",
            login_id="user.min",
            password="MinPass1"
        )
        assert request.password == "MinPass1"
    
    @pytest.mark.positive
    def test_valid_request_complex_password(self):
        """POSITIVE: Valid request with complex password."""
        request = AddUserRequest(
            username="User",
            login_id="user.complex",
            password="ComplexP@ss123!"
        )
        assert request.password == "ComplexP@ss123!"
    
    @pytest.mark.negative
    def test_invalid_empty_username(self):
        """NEGATIVE: Empty username."""
        with pytest.raises(ValidationError):
            AddUserRequest(
                username="",
                login_id="user.name",
                password="ValidPass123"
            )
    
    @pytest.mark.negative
    def test_invalid_missing_username(self):
        """NEGATIVE: Missing username field."""
        with pytest.raises(ValidationError):
            AddUserRequest(
                login_id="user.name",
                password="ValidPass123"
            )
    
    @pytest.mark.negative
    def test_invalid_none_username(self):
        """NEGATIVE: None as username."""
        with pytest.raises(ValidationError):
            AddUserRequest(
                username=None,
                login_id="user.name",
                password="ValidPass123"
            )
    
    @pytest.mark.negative
    def test_invalid_missing_login_id(self):
        """NEGATIVE: Missing login_id field."""
        with pytest.raises(ValidationError):
            AddUserRequest(
                username="User Name",
                password="ValidPass123"
            )
    
    @pytest.mark.negative
    def test_invalid_none_login_id(self):
        """NEGATIVE: None as login_id."""
        with pytest.raises(ValidationError):
            AddUserRequest(
                username="User Name",
                login_id=None,
                password="ValidPass123"
            )
    
    @pytest.mark.negative
    def test_invalid_missing_password(self):
        """NEGATIVE: Missing password field."""
        with pytest.raises(ValidationError):
            AddUserRequest(
                username="User Name",
                login_id="user.name"
            )
    
    @pytest.mark.negative
    def test_invalid_none_password(self):
        """NEGATIVE: None as password."""
        with pytest.raises(ValidationError):
            AddUserRequest(
                username="User Name",
                login_id="user.name",
                password=None
            )


class TestPasswordValidationInAddUserRequest:
    """Test password validation rules in AddUserRequest."""
    
    @pytest.mark.positive
    def test_password_with_uppercase_and_digit(self):
        """POSITIVE: Password with uppercase and digit."""
        request = AddUserRequest(
            username="User",
            login_id="user.pass",
            password="ValidPass123"
        )
        assert request.password == "ValidPass123"
    
    @pytest.mark.positive
    def test_password_complex_with_special_chars(self):
        """POSITIVE: Complex password with special characters."""
        request = AddUserRequest(
            username="User",
            login_id="user.pass2",
            password="SecureP@ss123!"
        )
        assert request.password == "SecureP@ss123!"
    
    @pytest.mark.positive
    def test_password_very_long(self):
        """POSITIVE: Very long password."""
        long_password = "ValidPass123" + "A" * 100
        request = AddUserRequest(
            username="User",
            login_id="user.longpass",
            password=long_password
        )
        assert request.password == long_password
    
    @pytest.mark.positive
    def test_password_no_uppercase_but_valid(self):
        """POSITIVE: Password without uppercase is accepted (no constraint)."""
        request = AddUserRequest(
            username="User",
            login_id="user.pass3",
            password="noupppercase123"
        )
        assert request.password == "noupppercase123"
    
    @pytest.mark.positive
    def test_password_no_digit_but_valid(self):
        """POSITIVE: Password without digit is accepted (no constraint)."""
        request = AddUserRequest(
            username="User",
            login_id="user.pass4",
            password="NoDigitsOnlyLetters"
        )
        assert request.password == "NoDigitsOnlyLetters"
    
    @pytest.mark.negative
    def test_password_too_short(self):
        """NEGATIVE: Password shorter than minimum."""
        with pytest.raises(ValidationError):
            AddUserRequest(
                username="User",
                login_id="user.pass5",
                password="Short1"
            )


class TestLoginIdValidationInAddUserRequest:
    """Test login_id validation rules in AddUserRequest."""
    
    @pytest.mark.positive
    def test_login_id_with_dots(self):
        """POSITIVE: login_id with dots."""
        request = AddUserRequest(
            username="User",
            login_id="user.name",
            password="ValidPass123"
        )
        assert request.login_id == "user.name"
    
    @pytest.mark.positive
    def test_login_id_with_hyphens(self):
        """POSITIVE: login_id with hyphens."""
        request = AddUserRequest(
            username="User",
            login_id="user-name",
            password="ValidPass123"
        )
        assert request.login_id == "user-name"
    
    @pytest.mark.positive
    def test_login_id_numeric(self):
        """POSITIVE: login_id with numbers."""
        request = AddUserRequest(
            username="User",
            login_id="user123",
            password="ValidPass123"
        )
        assert request.login_id == "user123"
    
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
    
    @pytest.mark.positive
    def test_login_id_with_consecutive_dots(self):
        """POSITIVE: login_id with multiple dots."""
        request = AddUserRequest(
            username="User",
            login_id="user.first.last",
            password="ValidPass123"
        )
        assert request.login_id == "user.first.last"
    
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
    
    @pytest.mark.negative
    def test_login_id_too_long(self):
        """NEGATIVE: login_id exceeds maximum length."""
        too_long_login = "a" * 51
        with pytest.raises(ValidationError):
            AddUserRequest(
                username="User",
                login_id=too_long_login,
                password="ValidPass123"
            )


class TestUsernameValidationInAddUserRequest:
    """Test username validation rules in AddUserRequest."""
    
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
    def test_username_with_unicode(self):
        """POSITIVE: Username with unicode characters."""
        request = AddUserRequest(
            username="José García",
            login_id="jose.garcia",
            password="ValidPass123"
        )
        assert request.username == "José García"
    
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


class TestEditUserRequestValidation:
    """Test EditUserRequest model validation."""
    
    @pytest.mark.positive
    def test_valid_edit_user_request_username(self):
        """POSITIVE: Edit user with valid username."""
        request = EditUserRequest(username="Updated Name")
        assert request.username == "Updated Name"
    
    @pytest.mark.positive
    def test_valid_edit_user_request_role(self):
        """POSITIVE: Edit user with valid role."""
        request = EditUserRequest(role="TELLER")
        assert request.role == "TELLER"
    
    @pytest.mark.positive
    def test_valid_edit_user_request_both_fields(self):
        """POSITIVE: Edit user with both username and role."""
        request = EditUserRequest(
            username="New Name",
            role="ADMIN"
        )
        assert request.username == "New Name"
        assert request.role == "ADMIN"
    
    @pytest.mark.positive
    def test_edit_user_request_empty_allowed(self):
        """POSITIVE: Edit user request with no fields is valid."""
        request = EditUserRequest()
        assert request.username is None
        assert request.role is None
    
    @pytest.mark.positive
    def test_edit_user_with_customer_role(self):
        """POSITIVE: Edit user with CUSTOMER role."""
        request = EditUserRequest(role="CUSTOMER")
        assert request.role == "CUSTOMER"
    
    @pytest.mark.positive
    def test_edit_user_with_admin_role(self):
        """POSITIVE: Edit user with ADMIN role."""
        request = EditUserRequest(role="ADMIN")
        assert request.role == "ADMIN"
    
    @pytest.mark.positive
    def test_invalid_edit_role_invalid_value_accepted(self):
        """POSITIVE: Edit user with invalid role is accepted (no validation)."""
        request = EditUserRequest(role="INVALID_ROLE")
        assert request.role == "INVALID_ROLE"
    
    @pytest.mark.positive
    def test_invalid_edit_role_lowercase_accepted(self):
        """POSITIVE: Edit user with lowercase role is accepted (no validation)."""
        request = EditUserRequest(role="admin")
        assert request.role == "admin"
    
    @pytest.mark.negative
    def test_invalid_edit_empty_username(self):
        """NEGATIVE: Edit user with empty username."""
        with pytest.raises(ValidationError):
            EditUserRequest(username="")
    
    @pytest.mark.negative
    def test_invalid_edit_username_exceeds_max(self):
        """NEGATIVE: Edit user with username exceeding max length."""
        with pytest.raises(ValidationError):
            EditUserRequest(username="A" * 256)


class TestValidRoleValues:
    """Test valid role values in EditUserRequest."""
    
    @pytest.mark.positive
    def test_role_customer_valid(self):
        """POSITIVE: CUSTOMER role is valid."""
        request = EditUserRequest(role="CUSTOMER")
        assert request.role == "CUSTOMER"
    
    @pytest.mark.positive
    def test_role_teller_valid(self):
        """POSITIVE: TELLER role is valid."""
        request = EditUserRequest(role="TELLER")
        assert request.role == "TELLER"
    
    @pytest.mark.positive
    def test_role_admin_valid(self):
        """POSITIVE: ADMIN role is valid."""
        request = EditUserRequest(role="ADMIN")
        assert request.role == "ADMIN"


class TestRoleValuesAccepted:
    """Test that various role values are accepted (no validation on role field)."""
    
    @pytest.mark.positive
    def test_role_superuser_accepted(self):
        """POSITIVE: SUPERUSER role is accepted (no validation)."""
        request = EditUserRequest(role="SUPERUSER")
        assert request.role == "SUPERUSER"
    
    @pytest.mark.positive
    def test_role_user_accepted(self):
        """POSITIVE: USER role is accepted (no validation)."""
        request = EditUserRequest(role="USER")
        assert request.role == "USER"
    
    @pytest.mark.positive
    def test_role_empty_string_accepted(self):
        """POSITIVE: Empty string role is accepted (no validation)."""
        request = EditUserRequest(role="")
        assert request.role == ""
    
    @pytest.mark.positive
    def test_role_mixed_case_accepted(self):
        """POSITIVE: Mixed case role is accepted (no validation)."""
        request = EditUserRequest(role="Customer")
        assert request.role == "Customer"
    
    @pytest.mark.positive
    def test_role_numeric_accepted(self):
        """POSITIVE: Numeric role is accepted (no validation)."""
        request = EditUserRequest(role="123")
        assert request.role == "123"


class TestEdgeCasesInAddUserRequest:
    """Test edge cases and boundary conditions in AddUserRequest."""
    
    @pytest.mark.positive
    def test_all_fields_with_special_values(self):
        """POSITIVE: All fields with special but valid values."""
        request = AddUserRequest(
            username="Test User!@#",
            login_id="test-user.123",
            password="SecurePass123"
        )
        assert request.username == "Test User!@#"
        assert request.login_id == "test-user.123"
        assert request.password == "SecurePass123"
    
    @pytest.mark.positive
    def test_password_with_long_uppercase_sequence(self):
        """POSITIVE: Password with long uppercase sequence."""
        request = AddUserRequest(
            username="User",
            login_id="user.long.upper",
            password="UPPERCASE123"
        )
        assert request.password == "UPPERCASE123"
    
    @pytest.mark.negative
    def test_all_fields_none(self):
        """NEGATIVE: All required fields are None."""
        with pytest.raises(ValidationError):
            AddUserRequest(
                username=None,
                login_id=None,
                password=None
            )
    
    @pytest.mark.positive
    def test_password_only_uppercase_and_special_accepted(self):
        """POSITIVE: Password with only uppercase and special chars is accepted (no constraint)."""
        request = AddUserRequest(
            username="User",
            login_id="user.pass",
            password="UPPERCASE@!"
        )
        assert request.password == "UPPERCASE@!"
    
    @pytest.mark.positive
    def test_password_only_lowercase_and_digit_accepted(self):
        """POSITIVE: Password with only lowercase and digit is accepted (no constraint)."""
        request = AddUserRequest(
            username="User",
            login_id="user.pass",
            password="lowercase123"
        )
        assert request.password == "lowercase123"


class TestRequestIntegration:
    """Test combinations of fields across different request types."""
    
    @pytest.mark.positive
    def test_add_user_then_edit_flow(self):
        """POSITIVE: Create request then simulate edit."""
        # Create a user
        create_req = AddUserRequest(
            username="Original Name",
            login_id="original.user",
            password="ValidPass123"
        )
        assert create_req.username == "Original Name"
        
        # Edit the user
        edit_req = EditUserRequest(
            username="Updated Name",
            role="TELLER"
        )
        assert edit_req.username == "Updated Name"
        assert edit_req.role == "TELLER"
    
    @pytest.mark.positive
    def test_multiple_valid_add_requests(self):
        """POSITIVE: Multiple valid add requests."""
        users = [
            AddUserRequest(
                username="User One",
                login_id="user.one",
                password="ValidPass123"
            ),
            AddUserRequest(
                username="User Two",
                login_id="user.two",
                password="StrongPass456"
            ),
            AddUserRequest(
                username="User Three",
                login_id="user.three",
                password="SecurePass789"
            )
        ]
        assert len(users) == 3
        assert all(u.username for u in users)
        assert all(u.login_id for u in users)
        assert all(u.password for u in users)
    
    @pytest.mark.positive
    def test_multiple_valid_edit_requests(self):
        """POSITIVE: Multiple valid edit requests."""
        edits = [
            EditUserRequest(username="Updated One"),
            EditUserRequest(role="TELLER"),
            EditUserRequest(username="Updated Two", role="ADMIN"),
        ]
        assert len(edits) == 3
        assert edits[0].username == "Updated One"
        assert edits[1].role == "TELLER"
        assert edits[2].username == "Updated Two"
        assert edits[2].role == "ADMIN"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
