"""Comprehensive tests for request models."""

import pytest
from pydantic import ValidationError
from app.models.request_models import AddUserRequest, EditUserRequest


class TestAddUserRequest:
    """Tests for AddUserRequest model."""

    @pytest.mark.positive
    def test_valid_add_user_request(self):
        """Test creating a valid AddUserRequest."""
        request = AddUserRequest(
            username="John Doe",
            login_id="john.doe",
            password="secure_password_123"
        )
        assert request.username == "John Doe"
        assert request.login_id == "john.doe"
        assert request.password == "secure_password_123"

    @pytest.mark.positive
    def test_add_user_request_with_special_characters_in_username(self):
        """Test username with special characters."""
        request = AddUserRequest(
            username="John O'Brien-Smith Jr.",
            login_id="john.brien.smith",
            password="password_123456"
        )
        assert request.username == "John O'Brien-Smith Jr."

    @pytest.mark.positive
    def test_add_user_request_with_min_length_username(self):
        """Test username with minimum length (1 character)."""
        request = AddUserRequest(
            username="A",
            login_id="a.user",
            password="password_123456"
        )
        assert request.username == "A"

    @pytest.mark.positive
    def test_add_user_request_with_max_length_username(self):
        """Test username with maximum length (255 characters)."""
        username = "A" * 255
        request = AddUserRequest(
            username=username,
            login_id="valid.login",
            password="password_123456"
        )
        assert request.username == username

    @pytest.mark.positive
    def test_add_user_request_with_numeric_login_id(self):
        """Test login_id with all numeric characters."""
        request = AddUserRequest(
            username="John Doe",
            login_id="12345",
            password="password_123456"
        )
        assert request.login_id == "12345"

    @pytest.mark.positive
    def test_add_user_request_with_dots_in_login_id(self):
        """Test login_id with dots."""
        request = AddUserRequest(
            username="John Doe",
            login_id="john.doe.smith",
            password="password_123456"
        )
        assert request.login_id == "john.doe.smith"

    @pytest.mark.positive
    def test_add_user_request_with_hyphens_in_login_id(self):
        """Test login_id with hyphens."""
        request = AddUserRequest(
            username="John Doe",
            login_id="john-doe-smith",
            password="password_123456"
        )
        assert request.login_id == "john-doe-smith"

    @pytest.mark.positive
    def test_add_user_request_with_underscores_in_login_id(self):
        """Test login_id with underscores."""
        request = AddUserRequest(
            username="John Doe",
            login_id="john_doe_smith",
            password="password_123456"
        )
        assert request.login_id == "john_doe_smith"

    @pytest.mark.positive
    def test_add_user_request_with_mixed_case_login_id(self):
        """Test login_id with mixed case."""
        request = AddUserRequest(
            username="John Doe",
            login_id="JohnDoeSmith",
            password="password_123456"
        )
        assert request.login_id == "JohnDoeSmith"

    @pytest.mark.positive
    def test_add_user_request_with_min_length_login_id(self):
        """Test login_id with minimum length (3 characters)."""
        request = AddUserRequest(
            username="John Doe",
            login_id="abc",
            password="password_123456"
        )
        assert request.login_id == "abc"

    @pytest.mark.positive
    def test_add_user_request_with_max_length_login_id(self):
        """Test login_id with maximum length (50 characters)."""
        login_id = "a" * 50
        request = AddUserRequest(
            username="John Doe",
            login_id=login_id,
            password="password_123456"
        )
        assert request.login_id == login_id

    @pytest.mark.positive
    def test_add_user_request_with_min_length_password(self):
        """Test password with minimum length (8 characters)."""
        request = AddUserRequest(
            username="John Doe",
            login_id="john.doe",
            password="pass1234"
        )
        assert request.password == "pass1234"

    @pytest.mark.positive
    def test_add_user_request_with_long_password(self):
        """Test password with long length."""
        password = "a" * 100
        request = AddUserRequest(
            username="John Doe",
            login_id="john.doe",
            password=password
        )
        assert request.password == password

    @pytest.mark.positive
    def test_add_user_request_with_special_chars_in_password(self):
        """Test password with special characters."""
        request = AddUserRequest(
            username="John Doe",
            login_id="john.doe",
            password="P@ssw0rd!#$%^&*()"
        )
        assert request.password == "P@ssw0rd!#$%^&*()"

    @pytest.mark.positive
    def test_add_user_request_with_spaces_in_password(self):
        """Test password with spaces."""
        request = AddUserRequest(
            username="John Doe",
            login_id="john.doe",
            password="pass word 123456"
        )
        assert request.password == "pass word 123456"

    @pytest.mark.negative
    def test_add_user_request_with_empty_username(self):
        """Test AddUserRequest with empty username."""
        with pytest.raises(ValidationError) as exc_info:
            AddUserRequest(
                username="",
                login_id="john.doe",
                password="password_123456"
            )
        assert "at least 1 character" in str(exc_info.value).lower()

    @pytest.mark.negative
    def test_add_user_request_with_username_exceeding_max_length(self):
        """Test AddUserRequest with username exceeding 255 characters."""
        with pytest.raises(ValidationError) as exc_info:
            AddUserRequest(
                username="A" * 256,
                login_id="john.doe",
                password="password_123456"
            )
        assert "at most 255 characters" in str(exc_info.value).lower()

    @pytest.mark.negative
    def test_add_user_request_with_none_username(self):
        """Test AddUserRequest with None username."""
        with pytest.raises(ValidationError):
            AddUserRequest(
                username=None,
                login_id="john.doe",
                password="password_123456"
            )

    @pytest.mark.negative
    def test_add_user_request_with_short_login_id(self):
        """Test AddUserRequest with login_id less than 3 characters."""
        with pytest.raises(ValidationError) as exc_info:
            AddUserRequest(
                username="John Doe",
                login_id="ab",
                password="password_123456"
            )
        assert "at least 3 characters" in str(exc_info.value).lower()

    @pytest.mark.negative
    def test_add_user_request_with_empty_login_id(self):
        """Test AddUserRequest with empty login_id."""
        with pytest.raises(ValidationError):
            AddUserRequest(
                username="John Doe",
                login_id="",
                password="password_123456"
            )

    @pytest.mark.negative
    def test_add_user_request_with_login_id_exceeding_max_length(self):
        """Test AddUserRequest with login_id exceeding 50 characters."""
        with pytest.raises(ValidationError) as exc_info:
            AddUserRequest(
                username="John Doe",
                login_id="a" * 51,
                password="password_123456"
            )
        assert "at most 50 characters" in str(exc_info.value).lower()

    @pytest.mark.negative
    def test_add_user_request_with_none_login_id(self):
        """Test AddUserRequest with None login_id."""
        with pytest.raises(ValidationError):
            AddUserRequest(
                username="John Doe",
                login_id=None,
                password="password_123456"
            )

    @pytest.mark.negative
    def test_add_user_request_with_spaces_in_login_id(self):
        """Test AddUserRequest with spaces in login_id."""
        with pytest.raises(ValidationError) as exc_info:
            AddUserRequest(
                username="John Doe",
                login_id="john doe",
                password="password_123456"
            )
        assert "alphanumeric" in str(exc_info.value).lower()

    @pytest.mark.negative
    def test_add_user_request_with_special_chars_in_login_id(self):
        """Test AddUserRequest with invalid special characters in login_id."""
        with pytest.raises(ValidationError) as exc_info:
            AddUserRequest(
                username="John Doe",
                login_id="john@doe!",
                password="password_123456"
            )
        assert "alphanumeric" in str(exc_info.value).lower()

    @pytest.mark.negative
    def test_add_user_request_with_hash_in_login_id(self):
        """Test AddUserRequest with hash in login_id."""
        with pytest.raises(ValidationError):
            AddUserRequest(
                username="John Doe",
                login_id="john#doe",
                password="password_123456"
            )

    @pytest.mark.negative
    def test_add_user_request_with_short_password(self):
        """Test AddUserRequest with password less than 8 characters."""
        with pytest.raises(ValidationError) as exc_info:
            AddUserRequest(
                username="John Doe",
                login_id="john.doe",
                password="pass123"
            )
        assert "at least 8 characters" in str(exc_info.value).lower()

    @pytest.mark.negative
    def test_add_user_request_with_empty_password(self):
        """Test AddUserRequest with empty password."""
        with pytest.raises(ValidationError):
            AddUserRequest(
                username="John Doe",
                login_id="john.doe",
                password=""
            )

    @pytest.mark.negative
    def test_add_user_request_with_none_password(self):
        """Test AddUserRequest with None password."""
        with pytest.raises(ValidationError):
            AddUserRequest(
                username="John Doe",
                login_id="john.doe",
                password=None
            )

    @pytest.mark.negative
    def test_add_user_request_with_missing_username(self):
        """Test AddUserRequest with missing username field."""
        with pytest.raises(ValidationError):
            AddUserRequest(
                login_id="john.doe",
                password="password_123456"
            )

    @pytest.mark.negative
    def test_add_user_request_with_missing_login_id(self):
        """Test AddUserRequest with missing login_id field."""
        with pytest.raises(ValidationError):
            AddUserRequest(
                username="John Doe",
                password="password_123456"
            )

    @pytest.mark.negative
    def test_add_user_request_with_missing_password(self):
        """Test AddUserRequest with missing password field."""
        with pytest.raises(ValidationError):
            AddUserRequest(
                username="John Doe",
                login_id="john.doe"
            )

    @pytest.mark.edge_case
    def test_add_user_request_with_unicode_in_username(self):
        """Test username with unicode characters."""
        request = AddUserRequest(
            username="José García",
            login_id="jose.garcia",
            password="password_123456"
        )
        assert request.username == "José García"

    @pytest.mark.edge_case
    def test_add_user_request_with_numeric_username(self):
        """Test username with only numeric characters."""
        request = AddUserRequest(
            username="123456",
            login_id="user.123",
            password="password_123456"
        )
        assert request.username == "123456"


class TestEditUserRequest:
    """Tests for EditUserRequest model."""

    @pytest.mark.positive
    def test_valid_edit_user_request_with_username_only(self):
        """Test EditUserRequest with only username."""
        request = EditUserRequest(username="Jane Doe")
        assert request.username == "Jane Doe"
        assert request.password is None

    @pytest.mark.positive
    def test_valid_edit_user_request_with_password_only(self):
        """Test EditUserRequest with only password."""
        request = EditUserRequest(password="new_secure_password_123")
        assert request.username is None
        assert request.password == "new_secure_password_123"

    @pytest.mark.positive
    def test_valid_edit_user_request_with_both_fields(self):
        """Test EditUserRequest with both username and password."""
        request = EditUserRequest(
            username="Jane Doe",
            password="new_secure_password_123"
        )
        assert request.username == "Jane Doe"
        assert request.password == "new_secure_password_123"

    @pytest.mark.positive
    def test_valid_edit_user_request_empty(self):
        """Test EditUserRequest with no fields (all None)."""
        request = EditUserRequest()
        assert request.username is None
        assert request.password is None

    @pytest.mark.positive
    def test_edit_user_request_with_min_length_username(self):
        """Test EditUserRequest with minimum username length."""
        request = EditUserRequest(username="A")
        assert request.username == "A"

    @pytest.mark.positive
    def test_edit_user_request_with_max_length_username(self):
        """Test EditUserRequest with maximum username length."""
        username = "A" * 255
        request = EditUserRequest(username=username)
        assert request.username == username

    @pytest.mark.positive
    def test_edit_user_request_with_min_length_password(self):
        """Test EditUserRequest with minimum password length."""
        request = EditUserRequest(password="pass1234")
        assert request.password == "pass1234"

    @pytest.mark.positive
    def test_edit_user_request_with_long_password(self):
        """Test EditUserRequest with long password."""
        password = "p" * 100
        request = EditUserRequest(password=password)
        assert request.password == password

    @pytest.mark.negative
    def test_edit_user_request_with_empty_username(self):
        """Test EditUserRequest with empty username."""
        with pytest.raises(ValidationError):
            EditUserRequest(username="")

    @pytest.mark.negative
    def test_edit_user_request_with_username_exceeding_max(self):
        """Test EditUserRequest with username exceeding 255 characters."""
        with pytest.raises(ValidationError):
            EditUserRequest(username="A" * 256)

    @pytest.mark.negative
    def test_edit_user_request_with_short_password(self):
        """Test EditUserRequest with password less than 8 characters."""
        with pytest.raises(ValidationError):
            EditUserRequest(password="pass123")

    @pytest.mark.negative
    def test_edit_user_request_with_empty_password(self):
        """Test EditUserRequest with empty password."""
        with pytest.raises(ValidationError):
            EditUserRequest(password="")

    @pytest.mark.edge_case
    def test_edit_user_request_with_unicode_username(self):
        """Test EditUserRequest with unicode characters in username."""
        request = EditUserRequest(username="François Müller")
        assert request.username == "François Müller"

    @pytest.mark.edge_case
    def test_edit_user_request_with_special_chars_in_password(self):
        """Test EditUserRequest with special characters in password."""
        password = "P@$$w0rd!@#$%^&*()"
        request = EditUserRequest(password=password)
        assert request.password == password
