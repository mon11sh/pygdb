"""
Transfer Limit Repository

Handles database operations for transfer limits and daily tracking.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
import asyncpg
from app.database.db import database
from app.models.enums import PrivilegeLevel
from app.exceptions.database_exception import DatabaseException

logger = logging.getLogger(__name__)


class TransferLimitRepositoryInterface(ABC):
    """Provider-agnostic data-access CONTRACT for transfer_limits + daily usage.

    get_daily_used_amount / get_daily_transaction_count MUST fail CLOSED on a
    DB error (raise DatabaseException) rather than returning 0, which would
    silently disable daily-limit enforcement.
    """

    @abstractmethod
    async def get_transfer_rule(self, privilege: str) -> Optional[Dict[str, Any]]:
        """Return {daily_limit, transaction_limit, created_at} or None."""

    @abstractmethod
    async def create_transfer_rule(
        self, privilege: str, daily_limit: Decimal, transaction_limit: int
    ) -> bool:
        """Insert or update a transfer limit rule (upsert)."""

    @abstractmethod
    async def get_daily_used_amount(
        self, account_number: int, date: Optional[datetime] = None
    ) -> Decimal:
        """Total amount transferred today from the account (fail CLOSED)."""

    @abstractmethod
    async def get_daily_transaction_count(
        self, account_number: int, date: Optional[datetime] = None
    ) -> int:
        """Number of transfers today from the account (fail CLOSED)."""


class TransferLimitRepository(TransferLimitRepositoryInterface):
    """Repository for transfer limit operations (asyncpg / postgres / supabase)."""

    @staticmethod
    async def get_transfer_rule(privilege: str) -> Optional[Dict[str, Any]]:
        """
        Get transfer limit rule for a privilege level.
        Queries the transfer_limits table.
        
        Args:
            privilege: Privilege level (PREMIUM, GOLD, SILVER)
            
        Returns:
            Dict with daily_limit, monthly_limit, transaction_limit
        """
        try:
            conn = await database.get_connection()
            try:
                query = """
                    SELECT * FROM transfer_limits 
                    WHERE privilege = $1
                """
                row = await conn.fetchrow(query, privilege)
                if row:
                    return {
                        "daily_limit": float(row['daily_limit']),
                        "transaction_limit": float(row['per_transaction_limit']),
                        "created_at": row['created_at']
                    }
                return None
            finally:
                await database._pool.release(conn)
        except Exception as e:
            logger.error(f"Error getting transfer rule: {str(e)}")
            return None

    @staticmethod
    async def create_transfer_rule(
        privilege: str, 
        daily_limit: Decimal, 
        transaction_limit: int
    ) -> bool:
        """
        Create or update a transfer limit rule.
        """
        try:
            conn = await database.get_connection()
            try:
                # Upsert rule
                query = """
                    INSERT INTO transfer_limits (privilege, daily_limit, per_transaction_limit)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (privilege) DO UPDATE 
                    SET daily_limit = EXCLUDED.daily_limit,
                        per_transaction_limit = EXCLUDED.per_transaction_limit,
                        updated_at = CURRENT_TIMESTAMP
                """
                await conn.execute(query, privilege, daily_limit, transaction_limit)
                return True
            finally:
                await database._pool.release(conn)
        except Exception as e:
            logger.error(f"Error creating/updating transfer rule: {str(e)}")
            raise

    @staticmethod
    async def get_daily_used_amount(
        account_number: int,
        date: Optional[datetime] = None
    ) -> Decimal:
        """
        Get total amount transferred today from the account.
        Queries fund_transfers table for all transactions from this account.
        
        Args:
            account_number: Account number
            date: Date to check (defaults to today)
            
        Returns:
            Total amount transferred today
        """
        if date is None:
            date = datetime.utcnow().date()
        
        try:
            conn = await database.get_connection()
            try:
                query = """
                    SELECT COALESCE(SUM(transfer_amount), 0) as total
                    FROM fund_transfers
                    WHERE from_account = $1
                    AND DATE(created_at) = $2
                """
                result = await conn.fetchrow(query, account_number, date)
                total = Decimal(str(result['total'])) if result else Decimal('0')
                logger.info(f"Daily used amount for account {account_number}: ₹{total}")
                return total
            finally:
                await database._pool.release(conn)
        except Exception as e:
            # Fail CLOSED: a lookup failure must block the transfer, never
            # silently return 0 (which would disable daily-limit enforcement
            # and allow unlimited transfers).
            logger.error(f"Error getting daily used amount: {str(e)}")
            raise DatabaseException("Failed to read daily used amount")


    @staticmethod
    async def get_daily_transaction_count(
        account_number: int,
        date: Optional[datetime] = None
    ) -> int:
        """
        Get number of transfers today from the account.
        Queries fund_transfers table for all transactions from this account.
        
        Args:
            account_number: Account number
            date: Date to check (defaults to today)
            
        Returns:
            Number of transactions today
        """
        if date is None:
            date = datetime.utcnow().date()
        
        try:
            conn = await database.get_connection()
            try:
                query = """
                    SELECT COUNT(*) as cnt
                    FROM fund_transfers
                    WHERE from_account = $1
                    AND DATE(created_at) = $2
                """
                result = await conn.fetchrow(query, account_number, date)
                count = result['cnt'] if result else 0
                logger.info(f"Daily transaction count for account {account_number}: {count}")
                return count
            finally:
                await database._pool.release(conn)
        except Exception as e:
            # Fail CLOSED: a lookup failure must block the transfer, never
            # silently return 0 (which would disable the daily transaction-count
            # limit and allow unlimited transfers).
            logger.error(f"Error getting daily transaction count: {str(e)}")
            raise DatabaseException("Failed to read daily transaction count")

