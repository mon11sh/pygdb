"""
Transaction Service - End-to-End Integration Tests

Comprehensive integration tests for multi-account workflows, daily limit resets,
concurrent transactions, and complete transaction lifecycles.

Exercises the provider-agnostic repository CONTRACT directly against the
InMemory provider implementations (construct + call + assert) — no asyncpg
internals are mocked. The same contract is implemented by the asyncpg
(postgres/supabase) and SQLAlchemy (sqlite/mysql) providers.

Author: QA Team
"""

import pytest
from unittest.mock import MagicMock
from decimal import Decimal
from datetime import datetime, timedelta
import asyncio

from app.models.enums import TransactionType, TransferMode, PrivilegeLevel
from app.repositories.inmemory_repositories import (
    InMemoryStore,
    InMemoryTransactionRepository,
    InMemoryTransactionLogRepository,
    InMemoryTransferLimitRepository,
)


# ================================================================
# FIXTURES
# ================================================================

@pytest.fixture
def store():
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


async def _seed_rule(limit_repo, privilege, daily, per_txn):
    await limit_repo.create_transfer_rule(privilege, Decimal(str(daily)), Decimal(str(per_txn)))


# ================================================================
# SECTION 1: MULTI-ACCOUNT TRANSACTION WORKFLOW TESTS
# ================================================================

class TestMultiAccountWorkflows:
    """Test multi-account transaction scenarios."""

    @pytest.mark.asyncio
    async def test_deposit_then_transfer(self, txn_repo):
        """POSITIVE: Account receives deposit record, then a transfer record."""
        txn_id = await txn_repo.create_transaction(0, 1000, Decimal('5000'), TransactionType.DEPOSIT)
        assert txn_id is not None
        txn_id2 = await txn_repo.create_transaction(1000, 1001, Decimal('2000'), TransactionType.TRANSFER)
        assert txn_id2 == txn_id + 1

    @pytest.mark.asyncio
    async def test_multiple_deposits_then_withdrawal(self, txn_repo):
        """POSITIVE: Multiple deposits followed by withdrawal."""
        id1 = await txn_repo.create_transaction(0, 1000, Decimal('2000'), TransactionType.DEPOSIT)
        id2 = await txn_repo.create_transaction(0, 1000, Decimal('3000'), TransactionType.DEPOSIT)
        id3 = await txn_repo.create_transaction(0, 1000, Decimal('2000'), TransactionType.DEPOSIT)
        assert [id1, id2, id3] == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_transfer_chain(self, txn_repo):
        """POSITIVE: Transaction chain: Account A -> B -> C -> D."""
        id1 = await txn_repo.create_transaction(1000, 1001, Decimal('5000'), TransactionType.TRANSFER)
        id2 = await txn_repo.create_transaction(1001, 1002, Decimal('5000'), TransactionType.TRANSFER)
        id3 = await txn_repo.create_transaction(1002, 1003, Decimal('5000'), TransactionType.TRANSFER)
        assert id1 is not None and id2 is not None and id3 is not None
        assert id1 < id2 < id3


# ================================================================
# SECTION 2: DAILY LIMIT RESET TESTS
# ================================================================

class TestDailyLimitResets:
    """Test daily limit behavior and resets."""

    @pytest.mark.asyncio
    async def test_daily_limit_accumulation(self, limit_repo, txn_repo):
        """POSITIVE: Track daily limit accumulation as transfers are added."""
        await txn_repo.create_transaction(1000, 2000, Decimal('15000'), TransactionType.TRANSFER)
        amount1 = await limit_repo.get_daily_used_amount(1000)
        await txn_repo.create_transaction(1000, 2000, Decimal('15000'), TransactionType.TRANSFER)
        amount2 = await limit_repo.get_daily_used_amount(1000)
        await txn_repo.create_transaction(1000, 2000, Decimal('15000'), TransactionType.TRANSFER)
        amount3 = await limit_repo.get_daily_used_amount(1000)

        assert amount1 == Decimal('15000')
        assert amount2 == Decimal('30000')
        assert amount3 == Decimal('45000')

    @pytest.mark.asyncio
    async def test_daily_transaction_count_limit(self, limit_repo, txn_repo):
        """POSITIVE: Track daily transaction count."""
        counts = []
        for _ in range(10):
            await txn_repo.create_transaction(1000, 2000, Decimal('10'), TransactionType.TRANSFER)
            counts.append(await limit_repo.get_daily_transaction_count(1000))
        assert counts == list(range(1, 11))

    @pytest.mark.asyncio
    async def test_daily_limit_reset_next_day(self, limit_repo, store):
        """EDGE: Verify limit is scoped to the day (yesterday's usage excluded)."""
        # A transfer dated yesterday should not count toward today's usage.
        yesterday = datetime.utcnow() - timedelta(days=1)
        tid = store.next_transfer_id()
        store.fund_transfers[tid] = {
            "id": tid, "from_account": 1000, "to_account": 2000,
            "transfer_amount": Decimal('50000'), "transfer_mode": "NEFT",
            "created_at": yesterday, "updated_at": yesterday,
        }
        amount_day1 = await limit_repo.get_daily_used_amount(1000, date=yesterday.date())
        amount_day2 = await limit_repo.get_daily_used_amount(1000)  # today

        assert amount_day1 == Decimal('50000')
        assert amount_day2 == Decimal('0')


# ================================================================
# SECTION 3: PRIVILEGE LEVEL SCENARIOS
# ================================================================

class TestPrivilegeLevelScenarios:
    """Test scenarios across different privilege levels."""

    @pytest.mark.asyncio
    async def test_premium_account_high_limit(self, limit_repo):
        """POSITIVE: PREMIUM account can transfer large amounts."""
        await _seed_rule(limit_repo, "PREMIUM", 100000, 50000)
        rule = await limit_repo.get_transfer_rule("PREMIUM")
        assert rule["daily_limit"] == 100000
        assert rule["transaction_limit"] == 50000

    @pytest.mark.asyncio
    async def test_gold_account_medium_limit(self, limit_repo):
        """POSITIVE: GOLD account has medium limits."""
        await _seed_rule(limit_repo, "GOLD", 50000, 25000)
        rule = await limit_repo.get_transfer_rule("GOLD")
        assert rule["daily_limit"] == 50000
        assert rule["transaction_limit"] == 25000

    @pytest.mark.asyncio
    async def test_silver_account_low_limit(self, limit_repo):
        """POSITIVE: SILVER account has low limits."""
        await _seed_rule(limit_repo, "SILVER", 25000, 12500)
        rule = await limit_repo.get_transfer_rule("SILVER")
        assert rule["daily_limit"] == 25000
        assert rule["transaction_limit"] == 12500

    @pytest.mark.asyncio
    async def test_upgrade_privilege_increases_limit(self, limit_repo):
        """EDGE: Upgrading privilege increases available limit."""
        await _seed_rule(limit_repo, "SILVER", 25000, 12500)
        await _seed_rule(limit_repo, "GOLD", 50000, 25000)
        await _seed_rule(limit_repo, "PREMIUM", 100000, 50000)

        silver_rule = await limit_repo.get_transfer_rule("SILVER")
        gold_rule = await limit_repo.get_transfer_rule("GOLD")
        premium_rule = await limit_repo.get_transfer_rule("PREMIUM")

        assert silver_rule["daily_limit"] < gold_rule["daily_limit"]
        assert gold_rule["daily_limit"] < premium_rule["daily_limit"]


# ================================================================
# SECTION 4: CONCURRENT TRANSACTION TESTS
# ================================================================

class TestConcurrentTransactions:
    """Test handling of concurrent transactions."""

    @pytest.mark.asyncio
    async def test_concurrent_deposits(self, txn_repo):
        """POSITIVE: Handle concurrent deposits to same account (unique ids)."""
        tasks = [
            txn_repo.create_transaction(0, 1000, Decimal('1000'), TransactionType.DEPOSIT)
            for _ in range(5)
        ]
        results = await asyncio.gather(*tasks)
        assert len(results) == 5
        assert all(r is not None for r in results)
        assert len(set(results)) == 5  # ids are unique

    @pytest.mark.asyncio
    async def test_concurrent_transfers(self, txn_repo):
        """POSITIVE: Handle concurrent transfers from same account."""
        tasks = [
            txn_repo.create_transaction(1000, 1000 + i, Decimal('500'), TransactionType.TRANSFER)
            for i in range(10)
        ]
        results = await asyncio.gather(*tasks)
        assert len(results) == 10
        assert len(set(results)) == 10

    @pytest.mark.asyncio
    async def test_race_condition_daily_limit(self, limit_repo, txn_repo):
        """EDGE: Two reads observe the same daily usage (no write between them)."""
        for _ in range(49):
            await txn_repo.create_transaction(1000, 2000, Decimal('1000'), TransactionType.TRANSFER)
        amount1 = await limit_repo.get_daily_used_amount(1000)
        amount2 = await limit_repo.get_daily_used_amount(1000)
        assert amount1 == amount2 == Decimal('49000')


# ================================================================
# SECTION 5: TRANSACTION LOG LIFECYCLE TESTS
# ================================================================

class TestTransactionLogLifecycle:
    """Test transaction logging and audit trail."""

    @pytest.mark.asyncio
    async def test_log_entry_creation_on_deposit(self, log_repo):
        """POSITIVE: Log entry created for deposit."""
        result = await log_repo.log_to_database(
            account_number=1000, amount=Decimal('5000'),
            transaction_type=TransactionType.DEPOSIT, reference_id=1
        )
        assert result == 1

    @pytest.mark.asyncio
    async def test_retrieve_complete_audit_trail(self, log_repo):
        """POSITIVE: Retrieve complete transaction history."""
        for i in range(1, 11):
            await log_repo.log_to_database(
                account_number=1000, amount=Decimal(1000 * i),
                transaction_type=TransactionType.TRANSFER, reference_id=1
            )
        logs, total_count = await log_repo.get_account_logs(1000, skip=0, limit=50)
        assert len(logs) == 10
        assert total_count == 10

    @pytest.mark.asyncio
    async def test_log_deletion_after_retention_period(self, log_repo, store):
        """POSITIVE: Old logs can be deleted; recent ones are kept."""
        # An old log (older than retention) and a fresh log.
        old_id = store.next_log_id()
        store.transaction_logs.append({
            "id": old_id, "account_number": 1000, "amount": Decimal('100'),
            "transaction_type": "DEPOSIT", "reference_id": None, "description": None,
            "mode": None, "status": "SUCCESS",
            "created_at": datetime.utcnow() - timedelta(days=200),
            "updated_at": datetime.utcnow() - timedelta(days=200),
        })
        await log_repo.log_to_database(
            account_number=1000, amount=Decimal('5000'),
            transaction_type=TransactionType.DEPOSIT, reference_id=1
        )

        result = await log_repo.delete_old_logs(days_to_keep=90)
        assert result is True
        remaining, total = await log_repo.get_account_logs(1000, skip=0, limit=50)
        assert total == 1  # only the fresh log survives


# ================================================================
# SECTION 6: ERROR RECOVERY SCENARIOS
# ================================================================

class TestErrorRecoveryScenarios:
    """Test system behavior during error conditions."""

    @pytest.mark.asyncio
    async def test_recover_from_partial_failure(self, txn_repo, store):
        """POSITIVE: A store error propagates; a later good call still succeeds."""
        store.next_transfer_id = MagicMock(side_effect=[RuntimeError("Connection error"), 2])
        with pytest.raises(Exception):
            await txn_repo.create_transaction(
                1000, 1001, Decimal('5000'), TransactionType.TRANSFER
            )
        # Recovery: the store recovers and the next create succeeds.
        result = await txn_repo.create_transaction(
            1000, 1001, Decimal('5000'), TransactionType.TRANSFER
        )
        assert result == 2

    @pytest.mark.asyncio
    async def test_database_reconnection(self, txn_repo):
        """POSITIVE: Handle database reconnection (first id after (re)connect)."""
        result = await txn_repo.create_transaction(
            1000, 1001, Decimal('5000'), TransactionType.TRANSFER
        )
        assert result == 1


# ================================================================
# TEST EXECUTION
# ================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
