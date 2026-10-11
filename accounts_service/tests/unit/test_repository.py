"""
Accounts Service - Repository Layer Comprehensive Tests

POSITIVE | NEGATIVE | EDGE CASES for all repository methods.

These tests exercise the provider-agnostic AccountRepository contract against the
InMemory implementation (DATABASE_PROVIDER=inmemory) directly — no mocking of a
database driver. Because the InMemory repository implements the exact same
contract as the SQLAlchemy repository (sqlite/mysql/postgres/supabase), these are
realistic, portable round-trip tests: construct the repo, call methods, assert.

Author: GDB Architecture Team
Version: 3.0.0
"""

import pytest
from decimal import Decimal
from datetime import datetime
from pydantic import ValidationError

from app.repositories.inmemory_repositories import (
    InMemoryStore,
    InMemoryAccountRepository,
)
from app.models.account import SavingsAccountCreate, CurrentAccountCreate, AccountUpdate
from app.exceptions.account_exceptions import DuplicateConstraintError

PIN_HASH = "hashed_pin"


@pytest.fixture
def repo():
    """A fresh InMemory AccountRepository (empty store) for each test."""
    return InMemoryAccountRepository(InMemoryStore())


def _savings(**overrides):
    data = dict(
        name="John Doe",
        pin="9640",
        date_of_birth="2000-01-15",
        gender="Male",
        phone_no="9876543210",
        aadhar_number="123456789012",
        privilege="GOLD",
    )
    data.update(overrides)
    return SavingsAccountCreate(**data)


def _current(**overrides):
    data = dict(
        name="Tech Corp",
        pin="5837",
        company_name="Tech Solutions Pvt Ltd",
        registration_no="REG12345678",
        privilege="PREMIUM",
    )
    data.update(overrides)
    return CurrentAccountCreate(**data)


# ================================================================
# CREATE SAVINGS ACCOUNT TESTS
# ================================================================

class TestCreateSavingsAccount:
    """Test create_savings_account method - all scenarios."""

    @pytest.mark.asyncio
    async def test_create_savings_account_success(self, repo):
        """POSITIVE: Create savings account with valid data."""
        result = await repo.create_savings_account(_savings(), PIN_HASH)
        assert result == 1000
        acc = await repo.get_account(1000)
        assert acc["account_type"] == "SAVINGS"
        assert acc["name"] == "John Doe"

    @pytest.mark.asyncio
    async def test_create_savings_account_with_premium_privilege(self, repo):
        """POSITIVE: Create with PREMIUM privilege."""
        result = await repo.create_savings_account(
            _savings(name="Jane Smith", privilege="PREMIUM"), PIN_HASH
        )
        assert result == 1000
        acc = await repo.get_account(result)
        assert acc["privilege"] == "PREMIUM"

    @pytest.mark.asyncio
    async def test_create_savings_account_with_silver_privilege(self, repo):
        """POSITIVE: Create with SILVER privilege."""
        result = await repo.create_savings_account(
            _savings(name="Bob Johnson", privilege="SILVER"), PIN_HASH
        )
        acc = await repo.get_account(result)
        assert acc["privilege"] == "SILVER"

    @pytest.mark.asyncio
    async def test_create_savings_account_female_gender(self, repo):
        """POSITIVE: Create with Female gender."""
        result = await repo.create_savings_account(
            _savings(name="Alice Wonder", gender="Female"), PIN_HASH
        )
        acc = await repo.get_account(result)
        assert acc["gender"] == "Female"

    @pytest.mark.asyncio
    async def test_create_savings_account_others_gender(self, repo):
        """POSITIVE: Create with Others gender."""
        result = await repo.create_savings_account(
            _savings(name="Alex Smith", gender="Others", privilege="SILVER"), PIN_HASH
        )
        acc = await repo.get_account(result)
        assert acc["gender"] == "Others"

    @pytest.mark.asyncio
    async def test_create_savings_account_duplicate_aadhar(self, repo):
        """NEGATIVE: Duplicate Aadhar raises DuplicateConstraintError."""
        await repo.create_savings_account(_savings(), PIN_HASH)
        with pytest.raises(DuplicateConstraintError):
            await repo.create_savings_account(
                _savings(name="Someone Else"), PIN_HASH
            )

    @pytest.mark.asyncio
    async def test_create_savings_account_very_long_name(self, repo):
        """EDGE: Create with very long name (255 chars)."""
        long_name = "A" * 255
        result = await repo.create_savings_account(_savings(name=long_name), PIN_HASH)
        assert result is not None
        assert isinstance(result, int)

    @pytest.mark.asyncio
    async def test_create_savings_account_min_length_name(self, repo):
        """EDGE: Name below minimum length (1 char) fails validation."""
        with pytest.raises(ValidationError):
            _savings(name="A")


# ================================================================
# CREATE CURRENT ACCOUNT TESTS
# ================================================================

class TestCreateCurrentAccount:
    """Test create_current_account method - all scenarios."""

    @pytest.mark.asyncio
    async def test_create_current_account_success(self, repo):
        """POSITIVE: Create current account with valid data."""
        result = await repo.create_current_account(_current(), PIN_HASH)
        assert result == 1000
        acc = await repo.get_account(result)
        assert acc["account_type"] == "CURRENT"
        assert acc["company_name"] == "Tech Solutions Pvt Ltd"

    @pytest.mark.asyncio
    async def test_create_current_account_with_website(self, repo):
        """POSITIVE: Create current account with website."""
        result = await repo.create_current_account(
            _current(website="https://techsolutions.com"), PIN_HASH
        )
        acc = await repo.get_account(result)
        assert acc["website"] == "https://techsolutions.com"

    @pytest.mark.asyncio
    async def test_create_current_account_gold_privilege(self, repo):
        """POSITIVE: Create with GOLD privilege."""
        result = await repo.create_current_account(
            _current(name="Finance Corp", registration_no="REG87654321", privilege="GOLD"),
            PIN_HASH,
        )
        acc = await repo.get_account(result)
        assert acc["privilege"] == "GOLD"

    @pytest.mark.asyncio
    async def test_create_current_account_silver_privilege(self, repo):
        """POSITIVE: Create with SILVER privilege."""
        result = await repo.create_current_account(
            _current(name="Small Business", registration_no="REG11111111", privilege="SILVER"),
            PIN_HASH,
        )
        acc = await repo.get_account(result)
        assert acc["privilege"] == "SILVER"

    @pytest.mark.asyncio
    async def test_create_current_account_without_website(self, repo):
        """POSITIVE: Create without website (optional field)."""
        result = await repo.create_current_account(
            _current(registration_no="REG99999999"), PIN_HASH
        )
        acc = await repo.get_account(result)
        assert acc["website"] is None

    @pytest.mark.asyncio
    async def test_create_current_account_duplicate_registration(self, repo):
        """NEGATIVE: Duplicate registration_no raises DuplicateConstraintError."""
        await repo.create_current_account(_current(), PIN_HASH)
        with pytest.raises(DuplicateConstraintError):
            await repo.create_current_account(_current(name="Another Corp"), PIN_HASH)

    @pytest.mark.asyncio
    async def test_create_current_account_special_chars_in_name(self, repo):
        """EDGE: Create with special characters in name."""
        result = await repo.create_current_account(
            _current(name="Tech-Corp & Co.", company_name="Tech-Solutions (Pvt) Ltd."),
            PIN_HASH,
        )
        acc = await repo.get_account(result)
        assert acc["name"] == "Tech-Corp & Co."


# ================================================================
# GET ACCOUNT TESTS
# ================================================================

class TestGetAccount:
    """Test get_account method - all scenarios."""

    @pytest.mark.asyncio
    async def test_get_account_success(self, repo):
        """POSITIVE: Retrieve existing account."""
        await repo.create_savings_account(_savings(), PIN_HASH)
        result = await repo.get_account(1000)
        assert result is not None
        assert result["account_number"] == 1000
        assert result["aadhar_number"] == "123456789012"

    @pytest.mark.asyncio
    async def test_get_account_zero_balance(self, repo):
        """EDGE: Retrieve account with zero balance (current account)."""
        await repo.create_current_account(_current(), PIN_HASH)
        result = await repo.get_account(1000)
        assert result is not None
        assert result["balance"] == 0.0

    @pytest.mark.asyncio
    async def test_get_account_large_balance(self, repo):
        """EDGE: Retrieve account with very large balance."""
        await repo.create_savings_account(_savings(initial_balance=999999999.99), PIN_HASH)
        result = await repo.get_account(1000)
        assert result is not None
        assert result["balance"] == 999999999.99

    @pytest.mark.asyncio
    async def test_get_account_not_found(self, repo):
        """NEGATIVE: Retrieve non-existent account returns None."""
        result = await repo.get_account(9999)
        assert result is None


# ================================================================
# UPDATE ACCOUNT TESTS
# ================================================================

class TestUpdateAccount:
    """Test update_account method - all scenarios."""

    @pytest.mark.asyncio
    async def test_update_account_name_only(self, repo):
        """POSITIVE: Update only account name."""
        await repo.create_savings_account(_savings(), PIN_HASH)
        updated = await repo.update_account(1000, {"name": "New Name"}, "SAVINGS")
        assert updated["name"] == "New Name"

    @pytest.mark.asyncio
    async def test_update_account_privilege_only(self, repo):
        """POSITIVE: Update only privilege."""
        await repo.create_savings_account(_savings(), PIN_HASH)
        updated = await repo.update_account(1000, {"privilege": "PREMIUM"}, "SAVINGS")
        assert updated["privilege"] == "PREMIUM"

    @pytest.mark.asyncio
    async def test_update_account_name_and_privilege(self, repo):
        """POSITIVE: Update both name and privilege."""
        await repo.create_savings_account(_savings(), PIN_HASH)
        updated = await repo.update_account(
            1000, {"name": "New Name", "privilege": "GOLD"}, "SAVINGS"
        )
        assert updated["name"] == "New Name"
        assert updated["privilege"] == "GOLD"

    @pytest.mark.asyncio
    async def test_update_account_empty_update(self, repo):
        """EDGE: Update with no fields (empty update) is a no-op."""
        await repo.create_savings_account(_savings(name="Original Name"), PIN_HASH)
        updated = await repo.update_account(1000, {}, "SAVINGS")
        assert updated["name"] == "Original Name"


# ================================================================
# DEBIT ACCOUNT TESTS
# ================================================================

class TestDebitAccount:
    """Test debit_account method - all scenarios."""

    @pytest.mark.asyncio
    async def test_debit_account_normal_amount(self, repo):
        """POSITIVE: Debit normal amount."""
        await repo.create_savings_account(_savings(initial_balance=50000.0), PIN_HASH)
        result = await repo.debit_account(1000, Decimal("5000.00"))
        assert result is True
        assert (await repo.get_account_balance(1000)) == 45000.0

    @pytest.mark.asyncio
    async def test_debit_account_small_amount(self, repo):
        """EDGE: Debit very small amount (0.01)."""
        await repo.create_savings_account(_savings(initial_balance=50000.0), PIN_HASH)
        result = await repo.debit_account(1000, Decimal("0.01"))
        assert result is True

    @pytest.mark.asyncio
    async def test_debit_account_insufficient_funds(self, repo):
        """NEGATIVE: Debit more than balance fails atomically (returns False)."""
        await repo.create_savings_account(_savings(initial_balance=2000.0), PIN_HASH)
        result = await repo.debit_account(1000, Decimal("999999.99"))
        assert result is False
        # Balance is untouched by a failed debit.
        assert (await repo.get_account_balance(1000)) == 2000.0

    @pytest.mark.asyncio
    async def test_debit_account_multiple_times(self, repo):
        """POSITIVE: Multiple sequential debits."""
        await repo.create_savings_account(_savings(initial_balance=50000.0), PIN_HASH)
        assert await repo.debit_account(1000, Decimal("1000.00")) is True
        assert await repo.debit_account(1000, Decimal("2000.00")) is True
        assert await repo.debit_account(1000, Decimal("3000.00")) is True
        assert (await repo.get_account_balance(1000)) == 44000.0


# ================================================================
# CREDIT ACCOUNT TESTS
# ================================================================

class TestCreditAccount:
    """Test credit_account method - all scenarios."""

    @pytest.mark.asyncio
    async def test_credit_account_normal_amount(self, repo):
        """POSITIVE: Credit normal amount."""
        await repo.create_savings_account(_savings(initial_balance=50000.0), PIN_HASH)
        result = await repo.credit_account(1000, Decimal("5000.00"))
        assert result is True
        assert (await repo.get_account_balance(1000)) == 55000.0

    @pytest.mark.asyncio
    async def test_credit_account_small_amount(self, repo):
        """EDGE: Credit very small amount (0.01)."""
        await repo.create_savings_account(_savings(initial_balance=50000.0), PIN_HASH)
        result = await repo.credit_account(1000, Decimal("0.01"))
        assert result is True

    @pytest.mark.asyncio
    async def test_credit_account_large_amount(self, repo):
        """EDGE: Credit large amount."""
        await repo.create_savings_account(_savings(initial_balance=2000.0), PIN_HASH)
        result = await repo.credit_account(1000, Decimal("999999999.99"))
        assert result is True

    @pytest.mark.asyncio
    async def test_credit_account_multiple_times(self, repo):
        """POSITIVE: Multiple sequential credits."""
        await repo.create_savings_account(_savings(initial_balance=50000.0), PIN_HASH)
        assert await repo.credit_account(1000, Decimal("1000.00")) is True
        assert await repo.credit_account(1000, Decimal("2000.00")) is True
        assert await repo.credit_account(1000, Decimal("3000.00")) is True
        assert (await repo.get_account_balance(1000)) == 56000.0


# ================================================================
# CLOSE ACCOUNT TESTS
# ================================================================

class TestCloseAccount:
    """Test close_account method - all scenarios."""

    @pytest.mark.asyncio
    async def test_close_account_success(self, repo):
        """POSITIVE: Close active account."""
        await repo.create_savings_account(_savings(), PIN_HASH)
        result = await repo.close_account(1000)
        assert result is True
        acc = await repo.get_account(1000)
        assert acc["is_active"] is False
        assert acc["closed_date"] is not None

    @pytest.mark.asyncio
    async def test_close_account_with_balance(self, repo):
        """EDGE: Close account that still has balance (allowed at repo level)."""
        await repo.create_savings_account(_savings(initial_balance=50000.0), PIN_HASH)
        result = await repo.close_account(1000)
        assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
