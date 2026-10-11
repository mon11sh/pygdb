"""
Transaction Service - Repository Layer Comprehensive Tests

Exercises the provider-agnostic repository CONTRACT directly against the
InMemory provider implementations (construct + call + assert) — no asyncpg
internals are mocked. The same contract is implemented by the asyncpg
(postgres/supabase) and SQLAlchemy (sqlite/mysql) providers.

Covers POSITIVE | NEGATIVE | EDGE cases for:
- TransactionRepository       (InMemoryTransactionRepository)
- TransactionLogRepository    (InMemoryTransactionLogRepository)
- TransferLimitRepository     (InMemoryTransferLimitRepository)

Author: QA Team
"""

import pytest
from unittest.mock import MagicMock
from decimal import Decimal
from datetime import datetime, timedelta

from app.repositories.inmemory_repositories import (
    InMemoryStore,
    InMemoryTransactionRepository,
    InMemoryTransactionLogRepository,
    InMemoryTransferLimitRepository,
)
from app.models.enums import TransactionType
from app.exceptions.transaction_exceptions import DatabaseException


# ================================================================
# FIXTURES
# ================================================================

@pytest.fixture
def store():
    """Fresh in-memory store per test."""
    return InMemoryStore()


@pytest.fixture
def txn_repo(store):
    return InMemoryTransactionRepository(store)


@pytest.fixture
def log_repo(store):
    return InMemoryTransactionLogRepository(store)


@pytest.fixture
def limit_repo(store):
    return InMemoryTransferLimitRepository(store)


# ================================================================
# SECTION 1: TRANSACTION REPOSITORY TESTS
# ================================================================

class TestTransactionRepository:
    """Test TransactionRepository.create_transaction and friends."""

    @pytest.mark.asyncio
    async def test_create_deposit_transaction(self, txn_repo):
        """POSITIVE: Create deposit transaction (from_account=0)."""
        transaction_id = await txn_repo.create_transaction(
            from_account=0, to_account=1000, amount=Decimal('5000'),
            transaction_type=TransactionType.DEPOSIT, description="Deposit"
        )
        assert transaction_id == 1
        row = await txn_repo.get_transaction(transaction_id)
        assert row["transfer_amount"] == Decimal('5000')

    @pytest.mark.asyncio
    async def test_create_withdrawal_transaction(self, txn_repo):
        """POSITIVE: Create withdrawal transaction (to_account=0)."""
        first = await txn_repo.create_transaction(
            from_account=1000, to_account=0, amount=Decimal('3000'),
            transaction_type=TransactionType.WITHDRAWAL, description="Withdrawal"
        )
        second = await txn_repo.create_transaction(
            from_account=1000, to_account=0, amount=Decimal('3000'),
            transaction_type=TransactionType.WITHDRAWAL, description="Withdrawal"
        )
        # Sequential ids
        assert first == 1
        assert second == 2

    @pytest.mark.asyncio
    async def test_create_transfer_transaction(self, txn_repo):
        """POSITIVE: Create transfer transaction (both accounts filled)."""
        transaction_id = await txn_repo.create_transaction(
            from_account=1000, to_account=1001, amount=Decimal('5000'),
            transaction_type=TransactionType.TRANSFER, description="Transfer"
        )
        assert transaction_id == 1
        row = await txn_repo.get_transaction(transaction_id)
        assert row["from_account"] == 1000 and row["to_account"] == 1001

    @pytest.mark.asyncio
    async def test_create_transaction_db_error(self, txn_repo, store):
        """NEGATIVE: A store error on create must propagate."""
        store.next_transfer_id = MagicMock(side_effect=RuntimeError("store down"))
        with pytest.raises(Exception):
            await txn_repo.create_transaction(
                from_account=1000, to_account=1001, amount=Decimal('5000'),
                transaction_type=TransactionType.TRANSFER
            )

    @pytest.mark.asyncio
    async def test_create_transaction_large_amount(self, txn_repo):
        """EDGE: Create transaction with very large amount (Decimal preserved)."""
        transaction_id = await txn_repo.create_transaction(
            from_account=1000, to_account=1001, amount=Decimal('999999999.99'),
            transaction_type=TransactionType.TRANSFER
        )
        row = await txn_repo.get_transaction(transaction_id)
        assert row["transfer_amount"] == Decimal('999999999.99')

    @pytest.mark.asyncio
    async def test_create_transaction_fractional_amount(self, txn_repo):
        """EDGE: Create transaction with fractional amount (Decimal preserved)."""
        transaction_id = await txn_repo.create_transaction(
            from_account=1000, to_account=1001, amount=Decimal('0.01'),
            transaction_type=TransactionType.TRANSFER
        )
        row = await txn_repo.get_transaction(transaction_id)
        assert row["transfer_amount"] == Decimal('0.01')


# ================================================================
# SECTION 2: TRANSACTION LOG REPOSITORY TESTS
# ================================================================

class TestTransactionLogRepository:
    """Test TransactionLogRepository methods."""

    @pytest.mark.asyncio
    async def test_log_to_database_success(self, log_repo):
        """POSITIVE: Successfully log to store, returns the generated id."""
        result = await log_repo.log_to_database(
            account_number=1000, amount=Decimal('5000'),
            transaction_type=TransactionType.TRANSFER, reference_id=1,
            description="Test transfer"
        )
        assert result == 1

    @pytest.mark.asyncio
    async def test_log_to_database_db_error(self, log_repo, store):
        """NEGATIVE: On store failure the repository returns None."""
        store.next_log_id = MagicMock(side_effect=RuntimeError("store down"))
        result = await log_repo.log_to_database(
            account_number=1000, amount=Decimal('5000'),
            transaction_type=TransactionType.TRANSFER, reference_id=1
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_get_account_logs_with_date_filter(self, log_repo):
        """POSITIVE: Get logs with date range filter."""
        for _ in range(2):
            await log_repo.log_to_database(
                account_number=1000, amount=Decimal('1000'),
                transaction_type=TransactionType.TRANSFER, reference_id=1
            )
        logs, total_count = await log_repo.get_account_logs(
            account_number=1000, skip=0, limit=50,
            start_date=datetime.utcnow() - timedelta(days=7),
            end_date=datetime.utcnow() + timedelta(days=1)
        )
        assert len(logs) == 2
        assert total_count == 2

    @pytest.mark.asyncio
    async def test_get_account_logs_no_results(self, log_repo):
        """POSITIVE: Get logs when no results found."""
        logs, total_count = await log_repo.get_account_logs(
            account_number=9999, skip=0, limit=50
        )
        assert len(logs) == 0
        assert total_count == 0

    @pytest.mark.asyncio
    async def test_get_account_logs_pagination(self, log_repo):
        """EDGE: Get logs with pagination."""
        for _ in range(100):
            await log_repo.log_to_database(
                account_number=1000, amount=Decimal('1000'),
                transaction_type=TransactionType.TRANSFER, reference_id=1
            )
        logs, total_count = await log_repo.get_account_logs(
            account_number=1000, skip=50, limit=1
        )
        assert len(logs) == 1
        assert total_count == 100


# ================================================================
# SECTION 3: TRANSFER LIMIT REPOSITORY TESTS
# ================================================================

async def _seed_rule(limit_repo, privilege, daily, per_txn):
    await limit_repo.create_transfer_rule(privilege, Decimal(str(daily)), Decimal(str(per_txn)))


class TestTransferLimitRepository:
    """Test TransferLimitRepository methods."""

    @pytest.mark.asyncio
    async def test_get_transfer_rule_premium(self, limit_repo):
        """POSITIVE: Get transfer rule for PREMIUM account."""
        await _seed_rule(limit_repo, "PREMIUM", 100000, 50000)
        rule = await limit_repo.get_transfer_rule("PREMIUM")
        assert rule is not None
        assert rule["daily_limit"] == 100000
        assert rule["transaction_limit"] == 50000

    @pytest.mark.asyncio
    async def test_get_transfer_rule_gold(self, limit_repo):
        """POSITIVE: Get transfer rule for GOLD account."""
        await _seed_rule(limit_repo, "GOLD", 50000, 25000)
        rule = await limit_repo.get_transfer_rule("GOLD")
        assert rule is not None
        assert rule["daily_limit"] == 50000
        assert rule["transaction_limit"] == 25000

    @pytest.mark.asyncio
    async def test_get_transfer_rule_silver(self, limit_repo):
        """POSITIVE: Get transfer rule for SILVER account."""
        await _seed_rule(limit_repo, "SILVER", 25000, 12500)
        rule = await limit_repo.get_transfer_rule("SILVER")
        assert rule is not None
        assert rule["daily_limit"] == 25000
        assert rule["transaction_limit"] == 12500

    @pytest.mark.asyncio
    async def test_get_transfer_rule_invalid_privilege(self, limit_repo):
        """NEGATIVE: Get rule for invalid privilege level."""
        rule = await limit_repo.get_transfer_rule("INVALID")
        assert rule is None

    @pytest.mark.asyncio
    async def test_get_transfer_rule_case_insensitive(self, limit_repo):
        """EDGE: Test case sensitivity (lower/upper both resolve)."""
        await _seed_rule(limit_repo, "PREMIUM", 100000, 50000)
        assert await limit_repo.get_transfer_rule("premium") is not None
        assert await limit_repo.get_transfer_rule("PREMIUM") is not None

    @pytest.mark.asyncio
    async def test_get_daily_used_amount(self, limit_repo, txn_repo):
        """POSITIVE: Get daily used amount for account."""
        await txn_repo.create_transaction(
            from_account=1000, to_account=2000, amount=Decimal('25000'),
            transaction_type=TransactionType.TRANSFER
        )
        amount = await limit_repo.get_daily_used_amount(account_number=1000)
        assert amount == Decimal('25000')

    @pytest.mark.asyncio
    async def test_get_daily_used_amount_no_transactions(self, limit_repo):
        """POSITIVE: Get daily used amount when no transactions."""
        amount = await limit_repo.get_daily_used_amount(account_number=9999)
        assert amount == Decimal('0')

    @pytest.mark.asyncio
    async def test_get_daily_transaction_count(self, limit_repo, txn_repo):
        """POSITIVE: Get daily transaction count."""
        for _ in range(15):
            await txn_repo.create_transaction(
                from_account=1000, to_account=2000, amount=Decimal('10'),
                transaction_type=TransactionType.TRANSFER
            )
        count = await limit_repo.get_daily_transaction_count(account_number=1000)
        assert count == 15

    @pytest.mark.asyncio
    async def test_get_daily_transaction_count_no_transactions(self, limit_repo):
        """POSITIVE: Get transaction count when no transactions."""
        count = await limit_repo.get_daily_transaction_count(account_number=9999)
        assert count == 0

    @pytest.mark.asyncio
    async def test_get_daily_amounts_db_error(self, limit_repo, store):
        """NEGATIVE: A store error must fail CLOSED (raise DatabaseException),
        not return 0 (which would silently disable daily-limit enforcement)."""
        broken = MagicMock()
        broken.values = MagicMock(side_effect=RuntimeError("store down"))
        store.fund_transfers = broken

        with pytest.raises(DatabaseException):
            await limit_repo.get_daily_used_amount(account_number=1000)

        with pytest.raises(DatabaseException):
            await limit_repo.get_daily_transaction_count(account_number=1000)


# ================================================================
# TEST EXECUTION
# ================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
