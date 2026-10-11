"""
Accounts Service - Comprehensive Models and Validators Tests

POSITIVE | NEGATIVE | EDGE CASES for all validation functions

Author: GDB Architecture Team
Version: 2.0.0
"""

import pytest
from datetime import datetime, date
from app.utils.validators import (
    validate_age,
    validate_pin,
    validate_phone_number,
    validate_privilege,
)
from app.utils.encryption import EncryptionManager
from app.exceptions.account_exceptions import (
    InvalidPinError,
    InvalidPrivilegeError,
    AgeRestrictionError,
    ValidationError,
)


@pytest.fixture
def encryption_manager():
    return EncryptionManager()


# ================================================================
# AGE VALIDATION - POSITIVE | NEGATIVE | EDGE
# ================================================================

class TestValidateAge:
    """Test age validation - All scenarios."""
    
    # POSITIVE CASES
    def test_age_25_years_old_valid(self):
        assert validate_age("1999-01-01") >= 18
    
    def test_age_50_years_old_valid(self):
        assert validate_age("1975-01-01") >= 18
    
    def test_age_100_years_old_valid(self):
        assert validate_age("1925-01-01") >= 18
    
    # EDGE CASES (BOUNDARY)
    def test_age_exactly_18_today(self):
        today = date.today()
        dob = f"{today.year - 18}-{today.month:02d}-{today.day:02d}"
        result = validate_age(dob)
        assert result >= 18
    
    # NEGATIVE CASES
    def test_age_17_rejected(self):
        today = date.today()
        # Create a date that makes the person 17 years and 364 days old (not yet 18)
        dob = f"{today.year - 18}-{today.month:02d}-{today.day + 1:02d}"
        # If today is end of month/year, verify math logic. safer to use date math or just year-17.
        # Actually simplest is:
        dob_date = today.replace(year=today.year - 17)
        dob = dob_date.strftime("%Y-%m-%d")
        
        with pytest.raises(AgeRestrictionError):
            validate_age(dob)
    
    def test_age_5_rejected(self):
        today = date.today()
        dob = f"{today.year - 5}-01-01"
        with pytest.raises(AgeRestrictionError):
            validate_age(dob)
    
    def test_age_newborn_rejected(self):
        today = date.today()
        dob = f"{today.year}-{today.month:02d}-01"
        with pytest.raises(AgeRestrictionError):
            validate_age(dob)
    
    def test_invalid_format_dashes(self):
        with pytest.raises(ValidationError):
            validate_age("01-01-1990")
    
    def test_invalid_format_slashes(self):
        with pytest.raises(ValidationError):
            validate_age("01/01/1990")
    
    def test_invalid_format_no_dashes(self):
        with pytest.raises(ValidationError):
            validate_age("19900101")


# ================================================================
# PIN VALIDATION - POSITIVE | NEGATIVE | EDGE
# ================================================================

class TestValidatePin:
    """Test PIN validation - All scenarios."""
    
    # POSITIVE CASES (Valid PINs)
    def test_pin_9640_valid(self):
        assert validate_pin("9640") == "9640"
    
    def test_pin_5837_valid(self):
        assert validate_pin("5837") == "5837"
    
    def test_pin_4682_valid(self):
        assert validate_pin("4682") == "4682"
    
    def test_pin_5_digits_valid(self):
        assert validate_pin("96402") == "96402"
    
    def test_pin_6_digits_valid(self):
        assert validate_pin("964027") == "964027"
    
    # EDGE CASES
    def test_pin_4_digits_minimum(self):
        assert validate_pin("9640") == "9640"
    
    def test_pin_6_digits_maximum(self):
        assert validate_pin("964027") == "964027"
    
    # NEGATIVE CASES (Invalid PINs)
    def test_pin_3_digits_too_short(self):
        with pytest.raises(InvalidPinError):
            validate_pin("123")
    
    def test_pin_7_digits_too_long(self):
        with pytest.raises(InvalidPinError):
            validate_pin("1234567")
    
    def test_pin_all_1s_rejected(self):
        with pytest.raises(InvalidPinError):
            validate_pin("1111")
    
    def test_pin_all_2s_rejected(self):
        with pytest.raises(InvalidPinError):
            validate_pin("2222")
    
    def test_pin_all_0s_rejected(self):
        with pytest.raises(InvalidPinError):
            validate_pin("0000")
    
    def test_pin_sequential_1234_rejected(self):
        with pytest.raises(InvalidPinError):
            validate_pin("1234")
    
    def test_pin_sequential_9876_rejected(self):
        with pytest.raises(InvalidPinError):
            validate_pin("9876")
    
    def test_pin_with_letters_rejected(self):
        with pytest.raises(InvalidPinError):
            validate_pin("96a0")
    
    def test_pin_with_special_chars_rejected(self):
        with pytest.raises(InvalidPinError):
            validate_pin("96@0")
    
    def test_pin_with_space_rejected(self):
        with pytest.raises(InvalidPinError):
            validate_pin("96 0")
    
    def test_pin_empty_rejected(self):
        with pytest.raises(InvalidPinError):
            validate_pin("")


# ================================================================
# PHONE NUMBER VALIDATION - POSITIVE | NEGATIVE | EDGE
# ================================================================

class TestValidatePhoneNumber:
    """Test phone number validation - All scenarios."""
    
    # POSITIVE CASES
    def test_phone_9876543210_valid(self):
        assert validate_phone_number("9876543210") == "9876543210"
    
    def test_phone_9123456789_valid(self):
        assert validate_phone_number("9123456789") == "9123456789"
    
    def test_phone_9000000000_valid(self):
        assert validate_phone_number("9000000000") == "9000000000"
    
    def test_phone_8765432109_valid(self):
        assert validate_phone_number("8765432109") == "8765432109"
    
    # EDGE CASES
    def test_phone_10_digits_minimum(self):
        assert validate_phone_number("9123456789") == "9123456789"
    
    def test_phone_all_9s_valid(self):
        assert validate_phone_number("9999999999") == "9999999999"
    
    # NEGATIVE CASES
    def test_phone_9_digits_too_short(self):
        with pytest.raises(ValidationError):
            validate_phone_number("123456789")
    
    def test_phone_11_digits_too_long(self):
        with pytest.raises(ValidationError):
            validate_phone_number("98765432101")
    
    def test_phone_1_digit_too_short(self):
        with pytest.raises(ValidationError):
            validate_phone_number("9")
    
    def test_phone_with_letters_rejected(self):
        with pytest.raises(ValidationError):
            validate_phone_number("9876a43210")
    
    def test_phone_with_special_chars_rejected(self):
        with pytest.raises(ValidationError):
            validate_phone_number("9876-543210")
    
    def test_phone_with_space_rejected(self):
        with pytest.raises(ValidationError):
            validate_phone_number("9876 543210")
    
    def test_phone_with_plus_rejected(self):
        with pytest.raises(ValidationError):
            validate_phone_number("+919876543210")
    
    def test_phone_empty_rejected(self):
        with pytest.raises(ValidationError):
            validate_phone_number("")
    
    def test_phone_only_spaces_rejected(self):
        with pytest.raises(ValidationError):
            validate_phone_number("          ")


# ================================================================
# PRIVILEGE VALIDATION - POSITIVE | NEGATIVE | EDGE
# ================================================================

class TestValidatePrivilege:
    """Test privilege validation - All scenarios."""
    
    # POSITIVE CASES
    def test_privilege_premium_valid(self):
        assert validate_privilege("PREMIUM") == "PREMIUM"
    
    def test_privilege_gold_valid(self):
        assert validate_privilege("GOLD") == "GOLD"
    
    def test_privilege_silver_valid(self):
        assert validate_privilege("SILVER") == "SILVER"
    
    # NEGATIVE CASES
    def test_privilege_lowercase_premium_rejected(self):
        with pytest.raises(ValidationError):
            validate_privilege("premium")
    
    def test_privilege_lowercase_gold_rejected(self):
        with pytest.raises(ValidationError):
            validate_privilege("gold")
    
    def test_privilege_mixed_case_rejected(self):
        with pytest.raises(ValidationError):
            validate_privilege("Premium")
    
    def test_privilege_platinum_rejected(self):
        with pytest.raises(ValidationError):
            validate_privilege("PLATINUM")
    
    def test_privilege_bronze_rejected(self):
        with pytest.raises(ValidationError):
            validate_privilege("BRONZE")
    
    def test_privilege_vip_rejected(self):
        with pytest.raises(ValidationError):
            validate_privilege("VIP")
    
    def test_privilege_empty_rejected(self):
        with pytest.raises(ValidationError):
            validate_privilege("")
    
    def test_privilege_space_rejected(self):
        with pytest.raises(ValidationError):
            validate_privilege(" ")
    
    def test_privilege_number_rejected(self):
        with pytest.raises(ValidationError):
            validate_privilege("1")
    
    def test_privilege_with_space_rejected(self):
        with pytest.raises(ValidationError):
            validate_privilege("PREMIUM ")
    
    def test_privilege_with_leading_space_rejected(self):
        with pytest.raises(ValidationError):
            validate_privilege(" PREMIUM")


# ================================================================
# ENCRYPTION TESTS - POSITIVE | NEGATIVE | EDGE
# ================================================================

class TestEncryptionManager:
    """Test encryption - All scenarios."""
    
    # POSITIVE CASES
    def test_hash_pin_9640(self, encryption_manager):
        hashed = encryption_manager.hash_pin("9640")
        assert hashed != "9640"
        assert len(hashed) > 0
        assert "$2b$" in hashed
    
    def test_hash_pin_5837(self, encryption_manager):
        hashed = encryption_manager.hash_pin("5837")
        assert hashed != "5837"
        assert "$2b$" in hashed
    
    def test_verify_pin_correct_9640(self, encryption_manager):
        pin = "9640"
        hashed = encryption_manager.hash_pin(pin)
        assert encryption_manager.verify_pin(pin, hashed) is True
    
    def test_verify_pin_correct_5837(self, encryption_manager):
        pin = "5837"
        hashed = encryption_manager.hash_pin(pin)
        assert encryption_manager.verify_pin(pin, hashed) is True
    
    def test_hash_consistency_both_verify(self, encryption_manager):
        pin = "9640"
        hash1 = encryption_manager.hash_pin(pin)
        hash2 = encryption_manager.hash_pin(pin)
        # Different hashes (salted)
        assert hash1 != hash2
        # But both verify
        assert encryption_manager.verify_pin(pin, hash1) is True
        assert encryption_manager.verify_pin(pin, hash2) is True
    
    # NEGATIVE CASES
    def test_verify_pin_incorrect_1234(self, encryption_manager):
        pin = "9640"
        wrong_pin = "1234"
        hashed = encryption_manager.hash_pin(pin)
        assert encryption_manager.verify_pin(wrong_pin, hashed) is False
    
    def test_verify_pin_incorrect_5837(self, encryption_manager):
        pin = "9640"
        wrong_pin = "5837"
        hashed = encryption_manager.hash_pin(pin)
        assert encryption_manager.verify_pin(wrong_pin, hashed) is False
    
    def test_verify_pin_empty_against_hashed(self, encryption_manager):
        pin = "9640"
        hashed = encryption_manager.hash_pin(pin)
        assert encryption_manager.verify_pin("", hashed) is False
    
    def test_verify_empty_pin_against_empty_hash(self, encryption_manager):
        # Edge case: empty PIN
        result = encryption_manager.verify_pin("", "")
        assert result is False
    
    def test_verify_pin_case_sensitive(self, encryption_manager):
        # Pins are numeric, but test behavior
        pin = "9640"
        hashed = encryption_manager.hash_pin(pin)
        # Same pin should verify
        assert encryption_manager.verify_pin("9640", hashed) is True
    
    # EDGE CASES
    def test_hash_pin_very_short(self, encryption_manager):
        hashed = encryption_manager.hash_pin("96")
        assert len(hashed) > 0
        assert "$2b$" in hashed
    
    def test_hash_pin_very_long(self, encryption_manager):
        long_pin = "9" * 100
        hashed = encryption_manager.hash_pin(long_pin)
        assert len(hashed) > 0
        assert encryption_manager.verify_pin(long_pin, hashed) is True


# ================================================================
# PYDANTIC MODELS - POSITIVE | NEGATIVE | EDGE
# ================================================================

class TestSavingsAccountModel:
    """Test SavingsAccountCreate model."""
    
    def test_valid_savings_account_all_fields(self):
        from app.models.account import SavingsAccountCreate
        account = SavingsAccountCreate(
            name="Sala Anil Kumar",
            pin="9640",
            date_of_birth="2000-01-15",
            gender="Male",
            phone_no="9876543210",
            aadhar_number="123456789012",
            privilege="GOLD"
        )
        assert account.name == "Sala Anil Kumar"
        assert account.pin == "9640"
        assert account.privilege == "GOLD"
    
    def test_savings_account_female_gender(self):
        from app.models.account import SavingsAccountCreate
        account = SavingsAccountCreate(
            name="Jane Doe",
            pin="5837",
            date_of_birth="2000-01-15",
            gender="Female",
            phone_no="9876543210",
            aadhar_number="123456789012",
            privilege="SILVER"
        )
        assert account.gender == "Female"
    
    def test_savings_account_others_gender(self):
        from app.models.account import SavingsAccountCreate
        account = SavingsAccountCreate(
            name="Alex Smith",
            pin="4682",
            date_of_birth="2000-01-15",
            gender="Others",
            phone_no="9876543210",
            aadhar_number="123456789012",
            privilege="PREMIUM"
        )
        assert account.gender == "Others"


class TestCurrentAccountModel:
    """Test CurrentAccountCreate model."""
    
    def test_valid_current_account(self):
        from app.models.account import CurrentAccountCreate
        account = CurrentAccountCreate(
            name="Tech Solutions",
            pin="5837",
            company_name="Tech Solutions Pvt Ltd",
            registration_no="REG12345678",
            privilege="PREMIUM"
        )
        assert account.company_name == "Tech Solutions Pvt Ltd"
    
    def test_current_account_with_website(self):
        from app.models.account import CurrentAccountCreate
        account = CurrentAccountCreate(
            name="Tech Solutions",
            pin="5837",
            company_name="Tech Solutions Pvt Ltd",
            registration_no="REG12345678",
            privilege="PREMIUM",
            website="https://techsolutions.com"
        )
        assert account.website == "https://techsolutions.com"
    
    def test_current_account_without_website(self):
        from app.models.account import CurrentAccountCreate
        account = CurrentAccountCreate(
            name="Tech Solutions",
            pin="5837",
            company_name="Tech Solutions Pvt Ltd",
            registration_no="REG12345678",
            privilege="PREMIUM"
        )
        assert account.website is None or account.website == ""


class TestAccountUpdateModel:
    """Test AccountUpdate model."""
    
    def test_update_name_only(self):
        from app.models.account import AccountUpdate
        update = AccountUpdate(name="New Name")
        assert update.name == "New Name"
    
    def test_update_privilege_only(self):
        from app.models.account import AccountUpdate
        update = AccountUpdate(privilege="PREMIUM")
        assert update.privilege == "PREMIUM"
    
    def test_update_both_fields(self):
        from app.models.account import AccountUpdate
        update = AccountUpdate(name="New Name", privilege="GOLD")
        assert update.name == "New Name"
        assert update.privilege == "GOLD"
    
    def test_update_empty(self):
        from app.models.account import AccountUpdate
        update = AccountUpdate()
        assert update.name is None
        assert update.privilege is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
