"""
Transaction Log Repository

Handles logging to both database and file system.
CRITICAL: Every transaction MUST be logged to both locations.
"""

import logging
import os
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
import asyncpg
from app.database.db import database
from app.models.enums import TransactionType
from app.config.settings import settings

logger = logging.getLogger(__name__)


class TransactionLogRepositoryInterface(ABC):
    """Provider-agnostic data-access CONTRACT for transaction_logging.

    The database methods are abstract (implemented per provider). The file-based
    logging helpers (log_to_file / read_file_logs) and the convenience wrappers
    (log_deposit / log_withdrawal / log_transfer) are provider-independent and
    shared as concrete methods so every implementation behaves identically.
    """

    @abstractmethod
    async def log_to_database(
        self,
        account_number: int,
        amount: Decimal,
        transaction_type: "TransactionType",
        reference_id: Optional[int] = None,
        description: Optional[str] = None,
    ) -> Optional[int]:
        """Insert a transaction_logging row. Returns the generated id or None."""

    @abstractmethod
    async def get_logs_for_transaction(self, transaction_id: int) -> Optional[Dict[str, Any]]:
        """Return {transaction_id, logs:[...]} for a reference id."""

    @abstractmethod
    async def get_account_logs(
        self,
        account_number: int,
        skip: int = 0,
        limit: int = 10,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        transaction_type: str = None,
        sort_by: str = "id",
        order: str = "asc",
    ) -> "tuple[List[Dict[str, Any]], int]":
        """Return (logs, total count) for an account with optional filters."""

    @abstractmethod
    async def get_all_transactions(
        self,
        skip: int = 0,
        limit: int = 50,
        transaction_type: str = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        sort_by: str = "id",
        order: str = "asc",
    ) -> List[Dict[str, Any]]:
        """Return combined transaction/transfer logs with optional filters."""

    @abstractmethod
    async def get_total_count(
        self,
        transaction_type: str = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """Total number of combined transactions with optional filters."""

    @abstractmethod
    async def delete_old_logs(self, days_to_keep: int = 90) -> bool:
        """Delete transaction_logging rows older than the cutoff."""

    # ---- Provider-independent shared behaviour -----------------------------

    @staticmethod
    def log_to_file(
        account_number: int,
        amount: Decimal,
        transaction_type: "TransactionType",
        reference_id: int,
        description: Optional[str] = None,
    ) -> bool:
        """Append a transaction line to the daily log file (YYYY-MM-DD.log)."""
        try:
            if not os.path.exists(settings.LOG_DIR):
                os.makedirs(settings.LOG_DIR, exist_ok=True)
            log_filename = datetime.utcnow().strftime(settings.LOG_FILE_FORMAT)
            log_filepath = os.path.join(settings.LOG_DIR, f"{log_filename}.log")
            timestamp = datetime.utcnow().isoformat()
            log_entry = (
                f"[{timestamp}] | "
                f"Account: {account_number} | "
                f"Type: {transaction_type.value} | "
                f"Amount: ₹{amount} | "
                f"RefID: {reference_id} | "
                f"Description: {description or 'N/A'}\n"
            )
            with open(log_filepath, "a", encoding="utf-8") as f:
                f.write(log_entry)
            logger.info(
                f"✅ Logged {transaction_type.value} for account {account_number} to file"
            )
            return True
        except IOError as e:
            logger.error(f"❌ Failed to log to file: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error logging to file: {str(e)}")
            return False

    @staticmethod
    def read_file_logs(days: int = 1) -> List[str]:
        """Read transaction log lines for a day (days back from today)."""
        try:
            log_date = datetime.utcnow() - timedelta(days=days)
            log_filename = log_date.strftime(settings.LOG_FILE_FORMAT)
            log_filepath = os.path.join(settings.LOG_DIR, f"{log_filename}.log")
            if not os.path.exists(log_filepath):
                logger.warning(f"Log file not found: {log_filepath}")
                return []
            with open(log_filepath, "r", encoding="utf-8") as f:
                return f.readlines()
        except Exception as e:
            logger.error(f"❌ Failed to read log file: {str(e)}")
            return []

    async def log_deposit(
        self, account_number: int, amount: Decimal, description: Optional[str] = None
    ) -> int:
        """Log a deposit to both the database and the daily file; returns 1.

        Args:
            account_number: Account being credited.
            amount: Deposit amount.
            description: Optional free-text description.

        Returns:
            The constant 1 (simplified log id).
        """
        await self.log_to_database(
            account_number=account_number, amount=amount,
            transaction_type=TransactionType.DEPOSIT, reference_id=0, description=description,
        )
        self.log_to_file(
            account_number=account_number, amount=amount,
            transaction_type=TransactionType.DEPOSIT, reference_id=0, description=description,
        )
        return 1

    async def log_withdrawal(
        self, account_number: int, amount: Decimal, description: Optional[str] = None
    ) -> int:
        """Log a withdrawal to both the database and the daily file; returns 1.

        Args:
            account_number: Account being debited.
            amount: Withdrawal amount.
            description: Optional free-text description.

        Returns:
            The constant 1 (simplified log id).
        """
        await self.log_to_database(
            account_number=account_number, amount=amount,
            transaction_type=TransactionType.WITHDRAWAL, reference_id=0, description=description,
        )
        self.log_to_file(
            account_number=account_number, amount=amount,
            transaction_type=TransactionType.WITHDRAWAL, reference_id=0, description=description,
        )
        return 1

    async def log_transfer(
        self, from_account: int, to_account: int, amount: Decimal,
        transfer_mode: str = "NEFT", description: Optional[str] = None,
    ) -> int:
        """Log a transfer to both the database and the daily file; returns 1.

        Args:
            from_account: Source account (the debited leg that is logged).
            to_account: Destination account.
            amount: Transfer amount.
            transfer_mode: Transfer mode (NEFT, RTGS, IMPS, etc.).
            description: Optional free-text description.

        Returns:
            The constant 1 (simplified log id).
        """
        await self.log_to_database(
            account_number=from_account, amount=amount,
            transaction_type=TransactionType.TRANSFER, reference_id=0, description=description,
        )
        self.log_to_file(
            account_number=from_account, amount=amount,
            transaction_type=TransactionType.TRANSFER, reference_id=0, description=description,
        )
        return 1


class TransactionLogRepository(TransactionLogRepositoryInterface):
    """Repository for transaction logging (asyncpg / postgres / supabase)."""

    @staticmethod
    async def log_to_database(
        account_number: int,
        amount: Decimal,
        transaction_type: TransactionType,
        reference_id: Optional[int] = None,
        description: Optional[str] = None
    ) -> Optional[int]:
        """
        Log transaction to database table.

        MANDATORY for all transactions.

        Args:
            account_number: Account involved
            amount: Transaction amount
            transaction_type: Type of transaction
            reference_id: Related fund_transfers id (for transfer legs)
            description: Optional description

        Returns:
            The generated log id on success, otherwise None.
        """
        query = """
            INSERT INTO transaction_logging (
                account_number, amount, transaction_type,
                reference_id, description, created_at
            )
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
        """

        try:
            conn = await database.get_connection()
            try:
                log_id = await conn.fetchval(
                    query,
                    account_number,
                    amount,  # Decimal → NUMERIC(15,2); no float round-trip (M-1)
                    transaction_type.value,
                    reference_id,
                    description,
                    datetime.utcnow()
                )
                logger.info(
                    f"✅ Logged {transaction_type.value} "
                    f"for account {account_number} to DB (ID: {log_id})"
                )
                return log_id
            finally:
                await database._pool.release(conn)
        except Exception as e:
            logger.error(f"❌ Failed to log to database: {str(e)}")
            return None

    @staticmethod
    def log_to_file(
        account_number: int,
        amount: Decimal,
        transaction_type: TransactionType,
        reference_id: int,
        description: Optional[str] = None
    ) -> bool:
        """
        Log transaction to file system.
        
        MANDATORY for all transactions.
        Creates daily log files: YYYY-MM-DD.log
        
        Args:
            account_number: Account involved
            amount: Transaction amount
            transaction_type: Type of transaction
            reference_id: Transaction ID reference
            description: Optional description
            
        Returns:
            True if logged successfully
        """
        try:
            # Ensure log directory exists
            if not os.path.exists(settings.LOG_DIR):
                os.makedirs(settings.LOG_DIR, exist_ok=True)
            
            # Generate file name with date
            log_filename = datetime.utcnow().strftime(settings.LOG_FILE_FORMAT)
            log_filepath = os.path.join(settings.LOG_DIR, f"{log_filename}.log")
            
            # Create log entry
            timestamp = datetime.utcnow().isoformat()
            log_entry = (
                f"[{timestamp}] | "
                f"Account: {account_number} | "
                f"Type: {transaction_type.value} | "
                f"Amount: ₹{amount} | "
                f"RefID: {reference_id} | "
                f"Description: {description or 'N/A'}\n"
            )
            
            # Append to file
            with open(log_filepath, 'a', encoding='utf-8') as f:
                f.write(log_entry)
            
            logger.info(
                f"✅ Logged {transaction_type.value} "
                f"for account {account_number} to file"
            )
            return True
            
        except IOError as e:
            logger.error(f"❌ Failed to log to file: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error logging to file: {str(e)}")
            return False

    @staticmethod
    async def get_logs_for_transaction(transaction_id: int) -> Optional[Dict[str, Any]]:
        """
        Get all logs for a specific transaction.
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            Transaction log dict or None
        """
        query = """
            SELECT * FROM transaction_logging
            WHERE reference_id = $1
            ORDER BY created_at DESC
        """
        
        conn = await database.get_connection()
        try:
            rows = await conn.fetch(query, transaction_id)
            return {
                "transaction_id": transaction_id,
                "logs": [dict(row) for row in rows]
            }
        finally:
            await database._pool.release(conn)

    @staticmethod
    async def get_account_logs(
        account_number: int,
        skip: int = 0,
        limit: int = 10,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        transaction_type: str = None,
        sort_by: str = 'id',
        order: str = 'asc'
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        Get all logs for an account with optional filtering and sorting.
        """
        # Build count query
        count_query = "SELECT COUNT(*) as count FROM transaction_logging WHERE account_number = $1"
        count_params = [account_number]
        
        # Build data query
        data_query = "SELECT * FROM transaction_logging WHERE account_number = $1"
        data_params = [account_number]
        
        param_idx = 2

        # Add transaction type filter
        if transaction_type and transaction_type != 'ALL':
            if transaction_type == 'WITHDRAW':
                 type_filter = " AND (transaction_type = 'WITHDRAW' OR transaction_type = 'WITHDRAWAL')"
                 count_query += type_filter
                 data_query += type_filter
            else:
                 count_query += f" AND transaction_type = ${param_idx}"
                 data_query += f" AND transaction_type = ${param_idx}"
                 count_params.append(transaction_type)
                 data_params.append(transaction_type)
                 param_idx += 1

        # Add date filters
        if start_date:
            count_query += f" AND created_at >= ${param_idx}"
            data_query += f" AND created_at >= ${param_idx}"
            count_params.append(start_date)
            data_params.append(start_date)
            param_idx += 1
        
        if end_date:
            count_query += f" AND created_at <= ${param_idx}"
            data_query += f" AND created_at <= ${param_idx}"
            count_params.append(end_date)
            data_params.append(end_date)
            param_idx += 1
        
        # Add sorting
        sort_column = 'id' if sort_by == 'id' else 'created_at'
        sort_direction = 'ASC' if order.lower() == 'asc' else 'DESC'
        
        # Add pagination
        data_query += f" ORDER BY {sort_column} {sort_direction} LIMIT ${param_idx} OFFSET ${param_idx + 1}"
        data_params.extend([limit, skip])
        
        conn = await database.get_connection()
        try:
            count_row = await conn.fetchrow(count_query, *count_params)
            total_count = count_row['count'] if count_row else 0
            
            rows = await conn.fetch(data_query, *data_params)
            logs = [dict(row) for row in rows]
            
            return logs, total_count
        finally:
            await database._pool.release(conn)
    
    @staticmethod
    async def get_all_transactions(
        skip: int = 0,
        limit: int = 50,
        transaction_type: str = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        sort_by: str = 'id',
        order: str = 'asc'
    ) -> List[Dict[str, Any]]:
        """
        Get all transaction logs with optional filtering.
        """
        # Determine sort clause
        sort_column = 'transaction_id' if sort_by == 'id' else 'timestamp'
        sort_direction = 'ASC' if order.lower() == 'asc' else 'DESC'
        order_clause = f"ORDER BY {sort_column} {sort_direction}"
        
        # Normalize transaction_type
        if transaction_type:
            transaction_type = str(transaction_type).upper()
            
        logger.info(f"Repository get_all_transactions: type={transaction_type!r}, dates={start_date}-{end_date}, sort={sort_by} {order}")

        # Helpers for dynamic params
        query_params = []
        param_idx = 1

        def add_param(val):
            """Append a value to the shared params list and return its positional placeholder (e.g. "$1")."""
            nonlocal param_idx
            query_params.append(val)
            idx = param_idx
            param_idx += 1
            return f"${idx}"

        # Build Date Clauses
        where_date_tl = ""
        where_date_ft = ""
        
        if start_date:
            p_start = add_param(start_date)
            where_date_tl += f" AND tl.created_at >= {p_start}"
            where_date_ft += f" AND ft.created_at >= {p_start}"
            
        if end_date:
            p_end = add_param(end_date)
            where_date_tl += f" AND tl.created_at <= {p_end}"
            where_date_ft += f" AND ft.created_at <= {p_end}"

        # Construct Query
        if not transaction_type or transaction_type == 'ALL':
            limit_ph = add_param(limit)
            offset_ph = add_param(skip)
            
            query = f"""
                SELECT * FROM (
                    SELECT 
                        tl.id as transaction_id,
                        tl.account_number,
                        NULL as from_account,
                        NULL as to_account,
                        tl.amount,
                        tl.transaction_type,
                        NULL as mode,
                        'SUCCESS' as status,
                        tl.created_at as timestamp
                    FROM transaction_logging tl
                    WHERE tl.transaction_type IN ('DEPOSIT', 'WITHDRAW', 'WITHDRAWAL')
                    {where_date_tl}
                    
                    UNION ALL
                    
                    SELECT 
                        ft.id as transaction_id,
                        NULL as account_number,
                        ft.from_account,
                        ft.to_account,
                        ft.transfer_amount as amount,
                        'TRANSFER' as transaction_type,
                        ft.transfer_mode as mode,
                        'SUCCESS' as status,
                        ft.created_at as timestamp
                    FROM fund_transfers ft
                    WHERE 1=1
                    {where_date_ft}
                ) as combined_transactions
                {order_clause}
                LIMIT {limit_ph} OFFSET {offset_ph}
            """
            
        elif transaction_type in ('DEPOSIT', 'WITHDRAW', 'WITHDRAWAL'):
            type_ph = add_param(transaction_type)
            limit_ph = add_param(limit)
            offset_ph = add_param(skip)
            
            query = f"""
                SELECT 
                    tl.id as transaction_id,
                    tl.account_number,
                    NULL as from_account,
                    NULL as to_account,
                    tl.amount,
                    tl.transaction_type,
                    NULL as mode,
                    'SUCCESS' as status,
                    tl.created_at as timestamp
                FROM transaction_logging tl
                WHERE (tl.transaction_type = {type_ph} OR ({type_ph} = 'WITHDRAW' AND tl.transaction_type = 'WITHDRAWAL'))
                {where_date_tl}
                {order_clause}
                LIMIT {limit_ph} OFFSET {offset_ph}
            """
            
        elif transaction_type == 'TRANSFER':
            # Reuse logic for TRANSFER
            limit_ph = add_param(limit)
            offset_ph = add_param(skip)
            
            query = f"""
                SELECT 
                    ft.id as transaction_id,
                    NULL as account_number,
                    ft.from_account,
                    ft.to_account,
                    ft.transfer_amount as amount,
                    'TRANSFER' as transaction_type,
                    ft.transfer_mode as mode,
                    'SUCCESS' as status,
                    ft.created_at as timestamp
                FROM fund_transfers ft
                WHERE 1=1
                {where_date_ft}
                {order_clause}
                LIMIT {limit_ph} OFFSET {offset_ph}
            """
        else:
            return []

        conn = await database.get_connection()
        try:
            rows = await conn.fetch(query, *query_params)
            return [dict(row) for row in rows]
        finally:
            await database._pool.release(conn)
    
    @staticmethod
    async def get_total_count(transaction_type: str = None, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> int:
        """
        Get total count with optional filtering.
        """
        if transaction_type:
            transaction_type = str(transaction_type).upper()

        query_params = []
        param_idx = 1

        def add_param(val):
            """Append a value to the shared params list and return its positional placeholder (e.g. "$1")."""
            nonlocal param_idx
            query_params.append(val)
            idx = param_idx
            param_idx += 1
            return f"${idx}"

        def get_date_cond(alias):
            """Build the date-range SQL condition for the given table alias, registering bound params."""
            cond = ""
            if start_date:
                ph = add_param(start_date)
                cond += f" AND {alias}.created_at >= {ph}"
            if end_date:
                ph = add_param(end_date)
                cond += f" AND {alias}.created_at <= {ph}"
            return cond
            
        # We need separate params list management carefully if we call get_date_cond twice
        # But here add_param appends to the SAME query_params list.
        # So $1 might be start_date for TL, $2 might be end_date for TL.
        # Then $3 start_date for FT, $4 end_date for FT.
        # This works correctly for a single execution.

        if not transaction_type or transaction_type == 'ALL':
             cond_tl = get_date_cond('tl')
             cond_ft = get_date_cond('ft')
             
             query = f"""
                SELECT 
                    (SELECT COUNT(*) FROM transaction_logging tl WHERE tl.transaction_type IN ('DEPOSIT', 'WITHDRAW', 'WITHDRAWAL') {cond_tl}) +
                    (SELECT COUNT(*) FROM fund_transfers ft WHERE 1=1 {cond_ft}) as count
            """
        elif transaction_type in ('DEPOSIT', 'WITHDRAW', 'WITHDRAWAL'):
             type_ph = add_param(transaction_type)
             cond_tl = get_date_cond('tl')
             query = f"SELECT COUNT(*) as count FROM transaction_logging tl WHERE (tl.transaction_type = {type_ph} OR ({type_ph} = 'WITHDRAW' AND tl.transaction_type = 'WITHDRAWAL')) {cond_tl}"
        elif transaction_type == 'TRANSFER':
             cond_ft = get_date_cond('ft')
             query = f"SELECT COUNT(*) as count FROM fund_transfers ft WHERE 1=1 {cond_ft}"
        else:
            return 0

        conn = await database.get_connection()
        try:
            row = await conn.fetchrow(query, *query_params)
            return row['count'] if row else 0
        finally:
            await database._pool.release(conn)

    @staticmethod
    def read_file_logs(days: int = 1) -> List[str]:
        """
        Read transaction logs from file system.
        
        Args:
            days: Number of days to read (0 = today, 1 = yesterday, etc.)
            
        Returns:
            List of log lines
        """
        try:
            log_date = datetime.utcnow() - timedelta(days=days)
            log_filename = log_date.strftime(settings.LOG_FILE_FORMAT)
            log_filepath = os.path.join(settings.LOG_DIR, f"{log_filename}.log")
            
            if not os.path.exists(log_filepath):
                logger.warning(f"Log file not found: {log_filepath}")
                return []
            
            with open(log_filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            return lines
            
        except Exception as e:
            logger.error(f"❌ Failed to read log file: {str(e)}")
            return []

    @staticmethod
    async def delete_old_logs(days_to_keep: int = 90) -> bool:
        """
        Delete transaction logs older than specified days.
        
        Args:
            days_to_keep: Number of days to keep
            
        Returns:
            True if successful
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        query = """
            DELETE FROM transaction_logging
            WHERE created_at < $1
        """
        
        try:
            conn = await database.get_connection()
            try:
                result = await conn.execute(query, cutoff_date)
                logger.info(f"✅ Deleted transaction logs older than {days_to_keep} days")
                return True
            finally:
                await database._pool.release(conn)
        except Exception as e:
            logger.error(f"❌ Failed to delete old logs: {str(e)}")
            return False

    @staticmethod
    async def log_deposit(
        account_number: int,
        amount: Decimal,
        description: Optional[str] = None
    ) -> int:
        """
        Log a deposit transaction.
        
        Args:
            account_number: Account being credited
            amount: Deposit amount
            description: Optional description
            
        Returns:
            Transaction ID for this log entry
        """
        await TransactionLogRepository.log_to_database(
            account_number=account_number,
            amount=amount,
            transaction_type=TransactionType.DEPOSIT,
            reference_id=0,  # Placeholder
            description=description
        )
        TransactionLogRepository.log_to_file(
            account_number=account_number,
            amount=amount,
            transaction_type=TransactionType.DEPOSIT,
            reference_id=0,
            description=description
        )
        return 1  # Simplified ID

    @staticmethod
    async def log_withdrawal(
        account_number: int,
        amount: Decimal,
        description: Optional[str] = None
    ) -> int:
        """
        Log a withdrawal transaction.
        
        Args:
            account_number: Account being debited
            amount: Withdrawal amount
            description: Optional description
            
        Returns:
            Transaction ID for this log entry
        """
        await TransactionLogRepository.log_to_database(
            account_number=account_number,
            amount=amount,
            transaction_type=TransactionType.WITHDRAWAL,
            reference_id=0,
            description=description
        )
        TransactionLogRepository.log_to_file(
            account_number=account_number,
            amount=amount,
            transaction_type=TransactionType.WITHDRAWAL,
            reference_id=0,
            description=description
        )
        return 1  # Simplified ID

    @staticmethod
    async def log_transfer(
        from_account: int,
        to_account: int,
        amount: Decimal,
        transfer_mode: str = "NEFT",
        description: Optional[str] = None
    ) -> int:
        """
        Log a transfer transaction.
        
        Args:
            from_account: Source account
            to_account: Destination account
            amount: Transfer amount
            transfer_mode: Transfer mode (NEFT, RTGS, IMPS, etc.)
            description: Optional description
            
        Returns:
            Transaction ID for this log entry
        """
        await TransactionLogRepository.log_to_database(
            account_number=from_account,
            amount=amount,
            transaction_type=TransactionType.TRANSFER,
            reference_id=0,
            description=description
        )
        TransactionLogRepository.log_to_file(
            account_number=from_account,
            amount=amount,
            transaction_type=TransactionType.TRANSFER,
            reference_id=0,
            description=description
        )
        return 1  # Simplified ID
