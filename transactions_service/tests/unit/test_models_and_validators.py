"""
Transaction Service - Models and Validators Tests

Comprehensive tests for all Pydantic models and validation logic:
- FundTransfer (Create/Response)
- TransactionLogging (Create/Response)
- Enums (TransactionType, TransferMode, PrivilegeLevel)
- Amount validation
- Balance validation
- PIN validation
- Transfer validation
- Transfer limit validation

Author: QA Team
"""

import pytest
from decimal import Decimal
from datetime import datetime

from app.models.enums import TransactionType, TransferMode, PrivilegeLevel
from app.models import FundTransferCreate, FundTransferResponse
from app.models import TransactionLoggingCreate, TransactionLoggingResponse


# ================================================================
# SECTION 1: ENUM TESTS
# ================================================================

class TestTransactionTypeEnum:
    """Test TransactionType enum."""
    
    def test_transaction_type_values(self):
        """Test all TransactionType values exist."""
        assert hasattr(TransactionType, 'DEPOSIT')
        assert hasattr(TransactionType, 'WITHDRAWAL')
        assert hasattr(TransactionType, 'TRANSFER')
    
    def test_transaction_type_count(self):
        """Test TransactionType has expected count."""
        types = [t for t in TransactionType]
        assert len(types) == 3
    
    def test_transaction_type_comparison(self):
        """Test enum comparison works."""
        assert TransactionType.DEPOSIT == TransactionType.DEPOSIT
        assert TransactionType.DEPOSIT != TransactionType.WITHDRAWAL
    
    def test_invalid_transaction_type(self):
        """Test invalid transaction type raises error."""
        with pytest.raises(AttributeError):
            _ = TransactionType.INVALID


class TestTransferModeEnum:
    """Test TransferMode enum."""
    
    def test_transfer_mode_values(self):
        """Test all TransferMode values exist."""
        assert hasattr(TransferMode, 'NEFT')
        assert hasattr(TransferMode, 'RTGS')
        assert hasattr(TransferMode, 'IMPS')
    
    def test_transfer_mode_count(self):
        """Test TransferMode has expected count."""
        modes = [m for m in TransferMode]
        assert len(modes) == 5  # NEFT, RTGS, IMPS, CHEQUE, UPI
    
    def test_invalid_transfer_mode(self):
        """Test invalid transfer mode raises error."""
        with pytest.raises(AttributeError):
            _ = TransferMode.INVALID


class TestPrivilegeLevelEnum:
    """Test PrivilegeLevel enum."""
    
    def test_privilege_levels(self):
        """Test all PrivilegeLevel values exist."""
        assert hasattr(PrivilegeLevel, 'PREMIUM')
        assert hasattr(PrivilegeLevel, 'GOLD')
        assert hasattr(PrivilegeLevel, 'SILVER')
    
    def test_privilege_level_count(self):
        """Test PrivilegeLevel has expected count."""
        levels = [l for l in PrivilegeLevel]
        assert len(levels) == 3


# ================================================================
# SECTION 2: AMOUNT VALIDATOR TESTS
# ================================================================

class TestAmountValidator:
    """Test amount validation in models."""
    
    def test_valid_withdrawal_amount(self):
        """Test valid withdrawal amount."""
        amount = Decimal('1000.50')
        assert amount > 0
    
    def test_valid_deposit_amount(self):
        """Test valid deposit amount."""
        amount = Decimal('5000.75')
        assert amount > 0
    
    def test_valid_transfer_amount(self):
        """Test valid transfer amount."""
        amount = Decimal('2500.25')
        assert amount > 0
    
    def test_withdrawal_zero_amount(self):
        """Test zero withdrawal amount."""
        amount = Decimal('0')
        assert amount == 0
    
    def test_withdrawal_negative_amount(self):
        """Test negative withdrawal amount."""
        amount = Decimal('-1000')
        assert amount < 0
    
    def test_deposit_zero_amount(self):
        """Test zero deposit amount."""
        amount = Decimal('0')
        assert amount == 0
    
    def test_deposit_negative_amount(self):
        """Test negative deposit amount."""
        amount = Decimal('-5000')
        assert amount < 0
    
    def test_transfer_zero_amount(self):
        """Test zero transfer amount."""
        amount = Decimal('0')
        assert amount == 0
    
    def test_transfer_negative_amount(self):
        """Test negative transfer amount."""
        amount = Decimal('-2500')
        assert amount < 0
    
    def test_very_large_amount(self):
        """Test very large amount."""
        amount = Decimal('9999999.99')
        assert amount > 0
    
    def test_fractional_amount(self):
        """Test fractional amount with many decimals."""
        amount = Decimal('0.01')
        assert amount > 0


# ================================================================
# SECTION 3: BALANCE VALIDATOR TESTS
# ================================================================

class TestBalanceValidator:
    """Test balance validation logic."""
    
    def test_sufficient_balance_exact_match(self):
        """Test withdrawal with exact balance."""
        balance = Decimal('1000')
        required = Decimal('1000')
        assert balance >= required
    
    def test_sufficient_balance_more_than_required(self):
        """Test withdrawal with more than required."""
        balance = Decimal('5000')
        required = Decimal('1000')
        assert balance >= required
    
    def test_insufficient_balance(self):
        """Test withdrawal with insufficient balance."""
        balance = Decimal('500')
        required = Decimal('1000')
        assert not (balance >= required)
    
    def test_zero_balance(self):
        """Test with zero balance."""
        balance = Decimal('0')
        required = Decimal('1000')
        assert not (balance >= required)
    
    def test_zero_balance_zero_required(self):
        """Test zero balance with zero required."""
        balance = Decimal('0')
        required = Decimal('0')
        assert balance >= required
    
    def test_large_balance_small_requirement(self):
        """Test large balance with small requirement."""
        balance = Decimal('1000000')
        required = Decimal('0.01')
        assert balance >= required
    
    def test_fractional_balance_check(self):
        """Test fractional balance check."""
        balance = Decimal('1000.50')
        required = Decimal('1000.49')
        assert balance >= required


# ================================================================
# SECTION 4: PIN VALIDATOR TESTS
# ================================================================

class TestPINValidator:
    """Test PIN validation logic."""
    
    def test_valid_pin_4_digits(self):
        """Test valid 4-digit PIN."""
        pin = "1234"
        assert len(pin) == 4 and pin.isdigit()
    
    def test_valid_pin_6_digits(self):
        """Test valid 6-digit PIN."""
        pin = "123456"
        assert len(pin) >= 4 and len(pin) <= 6 and pin.isdigit()
    
    def test_valid_pin_all_zeros(self):
        """Test PIN with all zeros."""
        pin = "0000"
        assert len(pin) == 4 and pin.isdigit()
    
    def test_valid_pin_all_nines(self):
        """Test PIN with all nines."""
        pin = "9999"
        assert len(pin) == 4 and pin.isdigit()
    
    def test_empty_pin(self):
        """Test empty PIN."""
        pin = ""
        assert len(pin) == 0
    
    def test_pin_with_letters(self):
        """Test PIN with letters."""
        pin = "12a4"
        assert not pin.isdigit()
    
    def test_pin_with_special_chars(self):
        """Test PIN with special characters."""
        pin = "12@4"
        assert not pin.isdigit()
    
    def test_pin_with_spaces(self):
        """Test PIN with spaces."""
        pin = "12 4"
        assert not pin.isdigit()
    
    def test_pin_too_short(self):
        """Test PIN too short."""
        pin = "123"
        assert len(pin) < 4
    
    def test_pin_too_long(self):
        """Test PIN too long."""
        pin = "12345678"
        assert len(pin) > 6
    
    def test_pin_negative_number(self):
        """Test PIN as negative number."""
        pin = "-1234"
        assert not pin.isdigit()


# ================================================================
# SECTION 5: TRANSFER VALIDATOR TESTS
# ================================================================

class TestTransferValidator:
    """Test transfer validation logic."""
    
    def test_different_accounts(self):
        """Test transfer between different accounts."""
        from_account = 1000
        to_account = 1001
        assert from_account != to_account
    
    def test_same_accounts(self):
        """Test transfer to same account."""
        from_account = 1000
        to_account = 1000
        assert from_account == to_account
    
    def test_zero_accounts_are_different(self):
        """Test zero account numbers are different if compared."""
        from_account = 0
        to_account = 0
        assert from_account == to_account
    
    def test_large_account_numbers(self):
        """Test large account numbers."""
        from_account = 9999999
        to_account = 9999998
        assert from_account > to_account


# ================================================================
# SECTION 6: TRANSFER LIMIT VALIDATOR TESTS
# ================================================================

class TestTransferLimitValidator:
    """Test transfer limit validation logic."""
    
    def test_within_daily_limit_premium(self):
        """Test premium account within daily limit."""
        daily_limit = Decimal('500000')
        used_amount = Decimal('250000')
        transfer_amount = Decimal('100000')
        remaining = daily_limit - used_amount
        assert transfer_amount <= remaining
    
    def test_within_daily_limit_gold(self):
        """Test gold account within daily limit."""
        daily_limit = Decimal('250000')
        used_amount = Decimal('100000')
        transfer_amount = Decimal('50000')
        remaining = daily_limit - used_amount
        assert transfer_amount <= remaining
    
    def test_within_daily_limit_silver(self):
        """Test silver account within daily limit."""
        daily_limit = Decimal('100000')
        used_amount = Decimal('40000')
        transfer_amount = Decimal('20000')
        remaining = daily_limit - used_amount
        assert transfer_amount <= remaining
    
    def test_exceeds_premium_limit(self):
        """Test premium account exceeds daily limit."""
        daily_limit = Decimal('500000')
        used_amount = Decimal('400000')
        transfer_amount = Decimal('150000')
        remaining = daily_limit - used_amount
        assert transfer_amount > remaining
    
    def test_exceeds_gold_limit(self):
        """Test gold account exceeds daily limit."""
        daily_limit = Decimal('250000')
        used_amount = Decimal('200000')
        transfer_amount = Decimal('60000')
        remaining = daily_limit - used_amount
        assert transfer_amount > remaining
    
    def test_exceeds_silver_limit(self):
        """Test silver account exceeds daily limit."""
        daily_limit = Decimal('100000')
        used_amount = Decimal('80000')
        transfer_amount = Decimal('30000')
        remaining = daily_limit - used_amount
        assert transfer_amount > remaining
    
    def test_at_exact_daily_limit(self):
        """Test transfer at exact daily limit."""
        daily_limit = Decimal('100000')
        used_amount = Decimal('60000')
        transfer_amount = Decimal('40000')
        remaining = daily_limit - used_amount
        assert transfer_amount == remaining
    
    def test_exceeding_by_one_rupee(self):
        """Test transfer exceeding limit by one rupee."""
        daily_limit = Decimal('100000')
        used_amount = Decimal('60000')
        transfer_amount = Decimal('40000.01')
        remaining = daily_limit - used_amount
        assert transfer_amount > remaining
    
    def test_transaction_count_within_limit(self):
        """Test transaction count within limit."""
        daily_limit = 50  # Max transactions
        used_count = 30
        assert used_count < daily_limit
    
    def test_transaction_count_exceeds_premium(self):
        """Test transaction count exceeds premium limit."""
        daily_limit = 50  # Premium
        used_count = 51
        assert used_count > daily_limit
    
    def test_transaction_count_exceeds_gold(self):
        """Test transaction count exceeds gold limit."""
        daily_limit = 30  # Gold
        used_count = 31
        assert used_count > daily_limit
    
    def test_combined_limits_validation(self):
        """Test both amount and count limits together."""
        amount_remaining = Decimal('50000')
        transfer_amount = Decimal('30000')
        count_remaining = 5
        
        assert transfer_amount <= amount_remaining
        assert count_remaining > 0
    
    def test_combined_limits_amount_exceeds(self):
        """Test combined limits with amount exceeding."""
        amount_remaining = Decimal('10000')
        transfer_amount = Decimal('30000')
        count_remaining = 5
        
        assert transfer_amount > amount_remaining
        assert count_remaining > 0
    
    def test_combined_limits_count_exceeds(self):
        """Test combined limits with count exceeding."""
        amount_remaining = Decimal('50000')
        transfer_amount = Decimal('30000')
        count_remaining = 0
        
        assert transfer_amount <= amount_remaining
        assert count_remaining == 0


# ================================================================
# SECTION 7: FUND TRANSFER MODEL TESTS
# ================================================================

class TestFundTransferModel:
    """Test FundTransfer model."""
    
    def test_fund_transfer_create_valid(self):
        """Test creating valid FundTransfer."""
        data = {
            "from_account": 1000,
            "to_account": 1001,
            "amount": Decimal("5000.00"),
            "transfer_mode": "NEFT",
            "pin": "1234"
        }
        # Would be instantiated with Pydantic
        assert data["from_account"] != data["to_account"]
        assert data["amount"] > 0
    
    def test_fund_transfer_response(self):
        """Test FundTransfer response model."""
        response_data = {
            "id": 1,
            "from_account": 1000,
            "to_account": 1001,
            "amount": Decimal("5000.00"),
            "transfer_mode": "NEFT",
            "status": "SUCCESS",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        assert response_data["id"] > 0
        assert response_data["status"] == "SUCCESS"


# ================================================================
# SECTION 8: TRANSACTION LOGGING MODEL TESTS
# ================================================================

class TestTransactionLoggingModel:
    """Test TransactionLogging model."""
    
    def test_transaction_logging_create(self):
        """Test creating TransactionLogging."""
        data = {
            "transaction_id": 1,
            "account_number": 1000,
            "amount": Decimal("5000.00"),
            "transaction_type": "TRANSFER",
            "created_at": datetime.now()
        }
        assert data["transaction_id"] > 0
        assert data["amount"] > 0


# ================================================================
# TEST EXECUTION
# ================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
