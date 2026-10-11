"""
Accounts Service - Service Layer Comprehensive Tests

POSITIVE | NEGATIVE | EDGE CASES for all service methods

Author: GDB Architecture Team
Version: 2.0.0
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from decimal import Decimal
from datetime import datetime, date
from app.services.account_service import AccountService
from app.models.account import SavingsAccountCreate, CurrentAccountCreate, AccountUpdate
from app.exceptions.account_exceptions import (
    AccountNotFoundError,
    AccountInactiveError,
    InsufficientFundsError,
    AgeRestrictionError,
    InvalidPinError,
)


@pytest.fixture
def mock_repository():
    """Mock repository."""
    return AsyncMock()


@pytest.fixture
def account_service(mock_repository):
    """Service with mocked repository and encryption."""
    with patch('app.services.account_service.AccountRepository') as mock_repo_class:
        with patch('app.services.account_service.EncryptionManager') as mock_enc_class:
            mock_repo_class.return_value = mock_repository
            
            # Mock encryption manager
            mock_encryption = AsyncMock()
            mock_encryption.hash_pin = MagicMock(return_value="$2b$12$hashed_pin")
            mock_encryption.verify_pin = MagicMock(return_value=True)
            mock_enc_class.return_value = mock_encryption
            
            service = AccountService()
            service.repo = mock_repository
            service.encryption = mock_encryption
            return service


# ================================================================
# CREATE SAVINGS ACCOUNT TESTS
# ================================================================

class TestCreateSavingsAccount:
    """Test create_savings_account method - all scenarios."""
    
    @pytest.mark.asyncio
    async def test_create_savings_account_success(self, account_service, mock_repository):
        """POSITIVE: Create savings account successfully."""
        account = SavingsAccountCreate(
            name="John Doe",
            pin="9640",
            date_of_birth="2000-01-15",
            gender="Male",
            phone_no="9876543210",
            aadhar_number="123456789012",
            privilege="GOLD"
        )
        mock_impl = AsyncMock()
        mock_impl.open = AsyncMock(return_value=1000)
        
        with patch('app.services.account_service.AccountFactory') as mock_factory_class:
            mock_factory = MagicMock()
            mock_factory.create.return_value = mock_impl
            mock_factory_class.return_value = mock_factory
            
            account_service.factory = mock_factory
            result = await account_service.create_savings_account(account)
            assert result == 1000
    
    @pytest.mark.asyncio
    async def test_create_savings_account_premium(self, account_service, mock_repository):
        """POSITIVE: Create with PREMIUM privilege."""
        account = SavingsAccountCreate(
            name="Jane Smith",
            pin="5837",
            date_of_birth="1995-05-20",
            gender="Female",
            phone_no="9123456789",
            aadhar_number="123456789012",
            privilege="PREMIUM"
        )
        mock_impl = AsyncMock()
        mock_impl.open = AsyncMock(return_value=1001)
        
        with patch('app.services.account_service.AccountFactory') as mock_factory_class:
            mock_factory = MagicMock()
            mock_factory.create.return_value = mock_impl
            mock_factory_class.return_value = mock_factory
            
            account_service.factory = mock_factory
            result = await account_service.create_savings_account(account)
            assert result == 1001
    
    @pytest.mark.asyncio
    async def test_create_savings_account_silver(self, account_service, mock_repository):
        """POSITIVE: Create with SILVER privilege."""
        account = SavingsAccountCreate(
            name="Bob Johnson",
            pin="4682",
            date_of_birth="1985-12-10",
            gender="Male",
            phone_no="8765432109",
            aadhar_number="123456789012",
            privilege="SILVER"
        )
        mock_impl = AsyncMock()
        mock_impl.open = AsyncMock(return_value=1002)
        
        with patch('app.services.account_service.AccountFactory') as mock_factory_class:
            mock_factory = MagicMock()
            mock_factory.create.return_value = mock_impl
            mock_factory_class.return_value = mock_factory
            
            account_service.factory = mock_factory
            result = await account_service.create_savings_account(account)
            assert result == 1002
    
    @pytest.mark.asyncio
    async def test_create_savings_account_edge_age_18(self, account_service, mock_repository):
        """EDGE: Create account for person exactly 18 years old."""
        today = date.today()
        dob = f"{today.year - 18}-{today.month:02d}-{today.day:02d}"
        
        account = SavingsAccountCreate(
            name="Young Adult",
            pin="9640",
            date_of_birth=dob,
            gender="Male",
            phone_no="9876543210",
            aadhar_number="123456789012",
            privilege="GOLD"
        )
        mock_impl = AsyncMock()
        mock_impl.open = AsyncMock(return_value=1003)
        
        with patch('app.services.account_service.AccountFactory') as mock_factory_class:
            mock_factory = MagicMock()
            mock_factory.create.return_value = mock_impl
            mock_factory_class.return_value = mock_factory
            
            account_service.factory = mock_factory
            result = await account_service.create_savings_account(account)
            assert result == 1003
    
        test_pins = ["9640", "5837", "4682", "8901", "1357"]
        names = ["John Doe", "Jane Smith", "Bob Johnson", "Alice Wonder", "Charlie Brown"]
        
        # Mock the factory to return a mock implementation that doesn't hit DB
        mock_impl = AsyncMock()
        
        with patch('app.services.account_service.AccountFactory') as mock_factory_class:
            mock_factory = MagicMock()
            mock_factory.create.return_value = mock_impl
            mock_factory_class.return_value = mock_factory
            
            # Re-initialize service with mocked factory
            account_service.factory = mock_factory
            
            for i, pin in enumerate(test_pins):
                mock_impl.open = AsyncMock(return_value=1000 + i)
                
                account = SavingsAccountCreate(
                    name=names[i],
                    pin=pin,
                    date_of_birth="2000-01-15",
                    gender="Male",
                    phone_no="9876543210",
                    aadhar_number="123456789012",
                    privilege="GOLD"
                )
                
                result = await account_service.create_savings_account(account)
                assert result == 1000 + i
    
        genders_and_names = [("Male", "John Smith"), ("Female", "Jane Doe"), ("Others", "Alex Taylor")]
        
        # Mock the factory to return a mock implementation that doesn't hit DB
        mock_impl = AsyncMock()
        
        with patch('app.services.account_service.AccountFactory') as mock_factory_class:
            mock_factory = MagicMock()
            mock_factory.create.return_value = mock_impl
            mock_factory_class.return_value = mock_factory
            
            # Re-initialize service with mocked factory
            account_service.factory = mock_factory
            
            for idx, (gender, name) in enumerate(genders_and_names):
                mock_impl.open = AsyncMock(return_value=2000 + idx)
                
                account = SavingsAccountCreate(
                    name=name,
                    pin="9640",
                    date_of_birth="2000-01-15",
                    gender=gender,
                    phone_no="9876543210",
                    aadhar_number="123456789012",
                    privilege="GOLD"
                )
                
                result = await account_service.create_savings_account(account)
                assert result == 2000 + idx


# ================================================================
# CREATE CURRENT ACCOUNT TESTS
# ================================================================

class TestCreateCurrentAccount:
    """Test create_current_account method - all scenarios."""
    
    @pytest.mark.asyncio
    async def test_create_current_account_success(self, account_service, mock_repository):
        """POSITIVE: Create current account successfully."""
        account = CurrentAccountCreate(
            name="Tech Corp",
            pin="5837",
            company_name="Tech Solutions Pvt Ltd",
            registration_no="REG12345678",
            privilege="PREMIUM"
        )
        # Mock the factory to return a mock implementation that doesn't hit DB
        mock_impl = AsyncMock()
        mock_impl.open = AsyncMock(return_value=2000)
        
        with patch('app.services.account_service.AccountFactory') as mock_factory_class:
            mock_factory = MagicMock()
            mock_factory.create.return_value = mock_impl
            mock_factory_class.return_value = mock_factory
            
            # Re-initialize service with mocked factory
            account_service.factory = mock_factory
            
            result = await account_service.create_current_account(account)
            assert result == 2000
    
    @pytest.mark.asyncio
    async def test_create_current_account_with_website(self, account_service, mock_repository):
        """POSITIVE: Create with website."""
        account = CurrentAccountCreate(
            name="Tech Corp",
            pin="5837",
            company_name="Tech Solutions Pvt Ltd",
            registration_no="REG12345678",
            privilege="PREMIUM",
            website="https://techsolutions.com"
        )
        # Mock the factory to return a mock implementation that doesn't hit DB
        mock_impl = AsyncMock()
        mock_impl.open = AsyncMock(return_value=2001)
        
        with patch('app.services.account_service.AccountFactory') as mock_factory_class:
            mock_factory = MagicMock()
            mock_factory.create.return_value = mock_impl
            mock_factory_class.return_value = mock_factory
            
            # Re-initialize service with mocked factory
            account_service.factory = mock_factory
            
            result = await account_service.create_current_account(account)
            assert result == 2001
    
    @pytest.mark.asyncio
    async def test_create_current_account_all_privileges(self, account_service, mock_repository):
        """POSITIVE: Create with all privilege levels."""
        for idx, privilege in enumerate(["PREMIUM", "GOLD", "SILVER"]):
            account = CurrentAccountCreate(
                name=f"Corp {privilege}",
                pin="5837",
                company_name=f"Company {privilege} Ltd",
                registration_no=f"REG{idx:08d}",
                privilege=privilege
            )
            # Mock the factory to return a mock implementation that doesn't hit DB
            mock_impl = AsyncMock()
            mock_impl.open = AsyncMock(return_value=2100 + idx)
            
            with patch('app.services.account_service.AccountFactory') as mock_factory_class:
                mock_factory = MagicMock()
                mock_factory.create.return_value = mock_impl
                mock_factory_class.return_value = mock_factory
                
                # Re-initialize service with mocked factory
                account_service.factory = mock_factory
                
                result = await account_service.create_current_account(account)
                assert result == 2100 + idx


# ================================================================
# DEBIT ACCOUNT TESTS
# ================================================================

class TestDebitAccount:
    """Test debit_account method - all scenarios."""
    
    @pytest.mark.asyncio
    async def test_debit_normal_amount(self, account_service, mock_repository):
        """POSITIVE: Debit normal amount."""
        # Mock get_account to return an active account
        # Repository returns account rows as dicts (asyncpg Record -> dict),
        # so the service accesses fields via dict keys.
        mock_account = {"is_active": True, "closed_date": None, "balance": Decimal("50000.00")}
        mock_repository.get_account = AsyncMock(return_value=mock_account)
        mock_repository.debit_account = AsyncMock(return_value=True)
        
        result = await account_service.debit_account(1000, Decimal("5000.00"))
        assert result is True
    
    @pytest.mark.asyncio
    async def test_debit_small_amount(self, account_service, mock_repository):
        """EDGE: Debit very small amount (0.01)."""
        # Repository returns account rows as dicts (asyncpg Record -> dict),
        # so the service accesses fields via dict keys.
        mock_account = {"is_active": True, "closed_date": None, "balance": Decimal("50000.00")}
        mock_repository.get_account = AsyncMock(return_value=mock_account)
        mock_repository.debit_account = AsyncMock(return_value=True)
        
        result = await account_service.debit_account(1000, Decimal("0.01"))
        assert result is True
    
    @pytest.mark.asyncio
    async def test_debit_large_amount(self, account_service, mock_repository):
        """POSITIVE: Debit large amount."""
        # Repository returns account rows as dicts (asyncpg Record -> dict),
        # so the service accesses fields via dict keys.
        mock_account = {"is_active": True, "closed_date": None, "balance": Decimal("50000.00")}
        mock_repository.get_account = AsyncMock(return_value=mock_account)
        mock_repository.debit_account = AsyncMock(return_value=True)
        
        result = await account_service.debit_account(1000, Decimal("50000.00"))
        assert result is True
    
    @pytest.mark.asyncio
    async def test_debit_sequential_amounts(self, account_service, mock_repository):
        """POSITIVE: Multiple sequential debits."""
        amounts = [Decimal("1000"), Decimal("2000"), Decimal("3000")]
        
        # Repository returns account rows as dicts (asyncpg Record -> dict),
        # so the service accesses fields via dict keys.
        mock_account = {"is_active": True, "closed_date": None, "balance": Decimal("50000.00")}
        mock_repository.get_account = AsyncMock(return_value=mock_account)
        mock_repository.debit_account = AsyncMock(return_value=True)
        
        for amount in amounts:
            result = await account_service.debit_account(1000, amount)
            assert result is True


# ================================================================
# CREDIT ACCOUNT TESTS
# ================================================================

class TestCreditAccount:
    """Test credit_account method - all scenarios."""
    
    @pytest.mark.asyncio
    async def test_credit_normal_amount(self, account_service, mock_repository):
        """POSITIVE: Credit normal amount."""
        # Repository returns account rows as dicts (asyncpg Record -> dict),
        # so the service accesses fields via dict keys.
        mock_account = {"is_active": True, "closed_date": None, "balance": Decimal("50000.00")}
        mock_repository.get_account = AsyncMock(return_value=mock_account)
        mock_repository.credit_account = AsyncMock(return_value=True)
        
        result = await account_service.credit_account(1000, Decimal("5000.00"))
        assert result is True
    
    @pytest.mark.asyncio
    async def test_credit_small_amount(self, account_service, mock_repository):
        """EDGE: Credit very small amount (0.01)."""
        # Repository returns account rows as dicts (asyncpg Record -> dict),
        # so the service accesses fields via dict keys.
        mock_account = {"is_active": True, "closed_date": None, "balance": Decimal("50000.00")}
        mock_repository.get_account = AsyncMock(return_value=mock_account)
        mock_repository.credit_account = AsyncMock(return_value=True)
        
        result = await account_service.credit_account(1000, Decimal("0.01"))
        assert result is True
    
    @pytest.mark.asyncio
    async def test_credit_large_amount(self, account_service, mock_repository):
        """POSITIVE: Credit large amount."""
        # Repository returns account rows as dicts (asyncpg Record -> dict),
        # so the service accesses fields via dict keys.
        mock_account = {"is_active": True, "closed_date": None, "balance": Decimal("50000.00")}
        mock_repository.get_account = AsyncMock(return_value=mock_account)
        mock_repository.credit_account = AsyncMock(return_value=True)
        
        result = await account_service.credit_account(1000, Decimal("950000.00"))
        assert result is True
    
    @pytest.mark.asyncio
    async def test_credit_sequential_amounts(self, account_service, mock_repository):
        """POSITIVE: Multiple sequential credits."""
        amounts = [Decimal("1000"), Decimal("2000"), Decimal("3000")]
        
        # Repository returns account rows as dicts (asyncpg Record -> dict),
        # so the service accesses fields via dict keys.
        mock_account = {"is_active": True, "closed_date": None, "balance": Decimal("50000.00")}
        mock_repository.get_account = AsyncMock(return_value=mock_account)
        mock_repository.credit_account = AsyncMock(return_value=True)
        
        for amount in amounts:
            result = await account_service.credit_account(1000, amount)
            assert result is True


# ================================================================
# UPDATE ACCOUNT TESTS
# ================================================================

class TestUpdateAccount:
    """Test update_account method - all scenarios."""
    
    @pytest.mark.asyncio
    async def test_update_name_only(self, account_service, mock_repository):
        """POSITIVE: Update name only."""
        mock_account = AsyncMock()
        mock_repository.get_account = AsyncMock(return_value=mock_account)
        mock_repository.update_account = AsyncMock(return_value=True)
        
        update = AccountUpdate(name="New Name")
        result = await account_service.update_account(1000, update)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_update_privilege_only(self, account_service, mock_repository):
        """POSITIVE: Update privilege only."""
        mock_account = AsyncMock()
        mock_repository.get_account = AsyncMock(return_value=mock_account)
        mock_repository.update_account = AsyncMock(return_value=True)
        
        update = AccountUpdate(privilege="PREMIUM")
        result = await account_service.update_account(1000, update)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_update_both_fields(self, account_service, mock_repository):
        """POSITIVE: Update both name and privilege."""
        mock_account = AsyncMock()
        mock_repository.get_account = AsyncMock(return_value=mock_account)
        mock_repository.update_account = AsyncMock(return_value=True)
        
        update = AccountUpdate(name="New Name", privilege="GOLD")
        result = await account_service.update_account(1000, update)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_update_empty(self, account_service, mock_repository):
        """EDGE: Update with no fields."""
        mock_account = AsyncMock()
        mock_repository.get_account = AsyncMock(return_value=mock_account)
        mock_repository.update_account = AsyncMock(return_value=True)
        
        update = AccountUpdate()
        result = await account_service.update_account(1000, update)
        # Since no fields to update, it returns early or calls repo with empty dict
        pass  # Just ensure no exception is raised


# ================================================================
# ACCOUNT STATUS TESTS
# ================================================================

class TestAccountStatus:
    """Test account status methods - all scenarios."""
    
    @pytest.mark.asyncio
    async def test_activate_account(self, account_service, mock_repository):
        """POSITIVE: Activate inactive account."""
        # Mock get_account to return an inactive account (dict, as repo returns)
        mock_account = {"is_active": False}
        mock_repository.get_account = AsyncMock(return_value=mock_account)
        mock_repository.activate_account = AsyncMock(return_value=True)
        
        result = await account_service.activate_account(1000)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_inactivate_account(self, account_service, mock_repository):
        """POSITIVE: Inactivate active account."""
        # Mock get_account to return an active account (dict, as repo returns)
        mock_account = {"is_active": True}
        mock_repository.get_account = AsyncMock(return_value=mock_account)
        mock_repository.inactivate_account = AsyncMock(return_value=True)
        
        result = await account_service.inactivate_account(1000)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_close_account(self, account_service, mock_repository):
        """POSITIVE: Close open account."""
        mock_account = {"balance": Decimal("0.00")}
        mock_repository.get_account = AsyncMock(return_value=mock_account)
        mock_repository.close_account = AsyncMock(return_value=True)
        
        result = await account_service.close_account(1000)
        assert result is True


# ================================================================
# PIN VERIFICATION TESTS
# ================================================================

class TestPinVerification:
    """Test PIN verification methods - all scenarios."""
    
    @pytest.mark.asyncio
    async def test_verify_pin_correct(self, account_service, mock_repository):
        """POSITIVE: Verify correct PIN."""
        mock_repository.get_pin_hash = AsyncMock(return_value="$2b$12$hashed_pin")
        account_service.encryption.verify_pin = MagicMock(return_value=True)
        
        result = await account_service.verify_pin(1000, "9640")
        assert result is True
    
    @pytest.mark.asyncio
    async def test_verify_pin_incorrect(self, account_service, mock_repository):
        """NEGATIVE: Verify incorrect PIN."""
        mock_repository.get_pin_hash = AsyncMock(return_value="$2b$12$hashed_pin")
        account_service.encryption.verify_pin = MagicMock(return_value=False)
        
        with pytest.raises(InvalidPinError):
            await account_service.verify_pin(1000, "0000")
    
    @pytest.mark.asyncio
    async def test_verify_pin_multiple_attempts(self, account_service, mock_repository):
        """POSITIVE: Multiple PIN verification attempts."""
        mock_repository.get_pin_hash = AsyncMock(return_value="$2b$12$hashed_pin")
        
        # Create a mock that tracks call count
        call_count = [0]
        
        def verify_side_effect(pin, hash):
            call_count[0] += 1
            # Return True on every other call (simulating pattern)
            return call_count[0] % 2 == 0
        
        account_service.encryption.verify_pin = MagicMock(side_effect=verify_side_effect)
        
        # Odd call (1st) returns False -> raises exception
        with pytest.raises(InvalidPinError):
            await account_service.verify_pin(1000, "1111")
        
        # Even call (2nd) returns True -> succeeds
        result = await account_service.verify_pin(1000, "9640")
        assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
