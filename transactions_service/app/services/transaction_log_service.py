"""
Transaction Log Service

Handles transaction logging operations (FE015-FE019).

Features:
- Query transaction logs for an account
- Query logs by date range
- Retrieve logs by reference ID
- Read file-based logs
- Delete old logs (archival)
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal

from app.exceptions.transaction_exceptions import (
    TransactionLogNotFoundException,
    AccountNotFoundException,
)
from app.models.enums import TransactionType
from app.repositories.transaction_log_repository import TransactionLogRepository
from app.integration.account_service_client import account_service_client

logger = logging.getLogger(__name__)


class TransactionLogService:
    """Service for transaction logging operations."""

    def __init__(self, log_repo: Optional[TransactionLogRepository] = None):
        """Initialize service with repositories."""
        self.log_repo = log_repo or TransactionLogRepository()
        self.account_client = account_service_client
    
    async def get_all_transactions(
        self,
        skip: int = 0,
        limit: int = 50,
        transaction_type: str = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        sort_by: str = 'id',
        order: str = 'asc'
    ) -> Dict[str, Any]:
        """
        Get all transaction logs (ADMIN/TELLER only).
        
        Args:
            skip: Pagination offset
            limit: Max results per page
            transaction_type: Optional filter by type
            start_date: Filter from date
            end_date: Filter to date
            sort_by: Field to sort by
            order: Sort direction
            
        Returns:
            Dict with logs and pagination info
        """
        logger.info(f"Getting all transactions: skip={skip}, limit={limit}, type={transaction_type}, dates={start_date}-{end_date}, sort={sort_by} {order}")
        
        # Get all logs from repository
        logs = await self.log_repo.get_all_transactions(
            skip=skip, 
            limit=limit, 
            transaction_type=transaction_type,
            start_date=start_date,
            end_date=end_date,
            sort_by=sort_by,
            order=order
        )
        
        # Get total count
        total = await self.log_repo.get_total_count(
            transaction_type=transaction_type,
            start_date=start_date,
            end_date=end_date
        )
        
        has_more = (skip + limit) < total
        
        return {
            "logs": logs,
            "skip": skip,
            "limit": limit,
            "total": total,
            "has_more": has_more,
        }

    async def get_transaction_logs(
        self,
        account_number: int,
        skip: int = 0,
        limit: int = 50,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        transaction_type: str = None,
        sort_by: str = 'id',
        order: str = 'asc'
    ) -> Dict[str, Any]:
        """
        Get transaction logs for an account.

        With optional date range filtering and sorting.

        Args:
            account_number: Account number
            skip: Pagination offset
            limit: Max results per page
            start_date: Filter from date (inclusive)
            end_date: Filter to date (inclusive)
            transaction_type: Filter by transaction type
            sort_by: Field to sort by
            order: Sort direction

        Returns:
            Dict with:
            - account_number: Requested account
            - logs: List of transaction logs
            - total_count: Total logs matching filter
            - skip: Pagination offset used
            - limit: Pagination limit used
            - has_more: Whether more results available

        Raises:
            AccountNotFoundException: If account doesn't exist
        """
        logger.info(
            f"📋 Fetching transaction logs for account {account_number} "
            f"(skip={skip}, limit={limit}, type={transaction_type}, sort={sort_by} {order})"
        )

        # STEP 1: Validate account exists
        await self.account_client.validate_account(account_number)

        # STEP 2: Get logs from database
        logs, total_count = await self.log_repo.get_account_logs(
            account_number=account_number,
            skip=skip,
            limit=limit,
            start_date=start_date,
            end_date=end_date,
            transaction_type=transaction_type,
            sort_by=sort_by,
            order=order
        )

        logger.info(f"✅ Retrieved {len(logs)} logs for account {account_number}")

        has_more = len(logs) == limit  # If we got exactly limit rows, there might be more

        return {
            "account_number": account_number,
            "logs": [
                {
                    "id": log.get("id"),
                    "account_number": log.get("account_number"),
                    "amount": float(log.get("amount", 0)),
                    "transaction_type": log.get("transaction_type"),
                    "created_at": log.get("created_at").isoformat() if log.get("created_at") else None,
                    "updated_at": log.get("updated_at").isoformat() if log.get("updated_at") else None,
                }
                for log in logs
            ],
            "skip": skip,
            "limit": limit,
            "has_more": has_more,
            "total_count": total_count,
        }

    async def get_logs_by_date_range(
        self, account_number: int, start_date: datetime, end_date: datetime, skip: int = 0, limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get logs for an account within a date range.

        Args:
            account_number: Account number
            start_date: Range start (inclusive)
            end_date: Range end (inclusive)
            skip: Pagination offset
            limit: Max results

        Returns:
            Dict with logs and pagination info

        Raises:
            AccountNotFoundException: If account doesn't exist
        """
        logger.info(
            f"📅 Fetching logs for account {account_number} "
            f"from {start_date.date()} to {end_date.date()}"
        )

        return await self.get_transaction_logs(
            account_number=account_number,
            skip=skip,
            limit=limit,
            start_date=start_date,
            end_date=end_date,
        )

    async def get_logs_by_reference_id(self, reference_id: str) -> Dict[str, Any]:
        """
        Get all logs for a specific transaction.

        Args:
            reference_id: Transaction ID

        Returns:
            Dict with:
            - reference_id: Transaction ID
            - logs: List of all logs for this transaction
            - count: Number of logs

        Raises:
            TransactionLogNotFoundException: If no logs found
        """
        logger.info(f"🔍 Fetching logs for transaction {reference_id}")

        logs = await self.log_repo.get_logs_for_transaction(reference_id)

        if not logs:
            raise TransactionLogNotFoundException(
                f"No logs found for transaction {reference_id}"
            )

        logger.info(f"✅ Retrieved {len(logs)} logs for transaction {reference_id}")

        return {
            "reference_id": reference_id,
            "logs": [
                {
                    "log_id": log.get("log_id"),
                    "account_number": log.get("account_number"),
                    "amount": float(log.get("amount", 0)),
                    "transaction_type": log.get("transaction_type"),
                    "status": log.get("status"),
                    "description": log.get("description"),
                    "created_at": log.get("created_at", "").isoformat() if log.get("created_at") else None,
                }
                for log in logs
            ],
            "count": len(logs),
        }

    async def get_file_logs(self, date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Read file-based transaction logs for a specific date.

        Useful for auditing and debugging.

        Args:
            date: Date to read logs for (defaults to today)

        Returns:
            Dict with:
            - date: Date of logs
            - file_path: Path to log file
            - log_lines: List of log lines
            - count: Number of log entries

        Raises:
            TransactionLogNotFoundException: If file doesn't exist
        """
        if date is None:
            date = datetime.utcnow()

        date_str = date.strftime("%Y-%m-%d")
        logger.info(f"📄 Reading file logs for {date_str}")

        logs = self.log_repo.read_file_logs(date)

        if not logs:
            raise TransactionLogNotFoundException(f"No logs found for date {date_str}")

        logger.info(f"✅ Read {len(logs)} lines from log file for {date_str}")

        return {
            "date": date_str,
            "log_lines": logs,
            "count": len(logs),
        }

    async def get_summary_stats(
        self, account_number: int, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get transaction summary statistics for an account.

        Args:
            account_number: Account number
            start_date: Filter from date
            end_date: Filter to date

        Returns:
            Dict with:
            - account_number: Account
            - total_transactions: Total count
            - successful_transactions: Count of SUCCESS
            - failed_transactions: Count of FAILED
            - total_amount_transferred: Sum of amounts
            - by_type: Breakdown by transaction type
            - date_range: Applied filters

        Raises:
            AccountNotFoundException: If account doesn't exist
        """
        logger.info(f"📊 Computing transaction summary for account {account_number}")

        # Validate account
        await self.account_client.validate_account(account_number)

        # Get all logs for period
        logs, total_count = await self.log_repo.get_account_logs(
            account_number=account_number,
            skip=0,
            limit=10000,  # Get all
            start_date=start_date,
            end_date=end_date,
        )

        # Compute stats
        total = len(logs)
        successful = len([l for l in logs if l.get("status") == "SUCCESS"])
        failed = len([l for l in logs if l.get("status") == "FAILED"])
        total_amount = Decimal(0)

        by_type = {
            TransactionType.DEPOSIT.value: 0,
            TransactionType.WITHDRAWAL.value: 0,
            TransactionType.TRANSFER.value: 0,
        }

        total_credits = Decimal(0)
        total_debits = Decimal(0)

        for log in logs:
            amount = Decimal(str(log.get("amount", 0)))
            total_amount += amount
            txn_type = log.get("transaction_type", "UNKNOWN")
            
            if txn_type in by_type:
                by_type[txn_type] += 1
                
            # Calculate credits and debits
            if txn_type == TransactionType.DEPOSIT.value:
                total_credits += amount
            elif txn_type in (TransactionType.WITHDRAWAL.value, TransactionType.TRANSFER.value):
                total_debits += amount

        logger.info(f"✅ Summary computed - {total} txns, Credits: ₹{total_credits}, Debits: ₹{total_debits}")

        return {
            "account_number": account_number,
            "total_transactions": total,
            "successful_transactions": successful,
            "failed_transactions": failed,
            "total_amount_transferred": float(total_amount),
            "total_credits": float(total_credits),
            "total_debits": float(total_debits),
            "by_type": by_type,
            "date_range": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None,
            },
        }

    async def delete_old_logs(self, days_to_keep: int = 90) -> Dict[str, Any]:
        """
        Delete transaction logs older than specified days.

        Admin operation for archival/cleanup.

        Args:
            days_to_keep: Keep logs from last N days (delete older)

        Returns:
            Dict with:
            - deleted_count: Number of records deleted
            - cutoff_date: Logs before this date were deleted

        Raises:
            None (logs won't error if nothing to delete)
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

        logger.info(f"🗑️ Deleting transaction logs before {cutoff_date.date()}")

        deleted_count = await self.log_repo.delete_old_logs(cutoff_date)

        logger.info(f"✅ Deleted {deleted_count} old transaction logs")

        return {
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.isoformat(),
            "days_to_keep": days_to_keep,
        }


# Singleton instance
transaction_log_service = TransactionLogService()
