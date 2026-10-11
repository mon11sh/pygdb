"""
Transfer Limit Service

Handles transfer limit operations (FE013, FE014).

Features:
- Get transfer limits for an account (based on privilege level)
- Get remaining transfer limit (daily_limit - daily_used)
- Get transfer count limits (daily_count - daily_transactions)
- Get all transfer rules (for admin)
- Validate against limits (delegated to validator)
"""

import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal

from app.exceptions.transaction_exceptions import (
    AccountNotFoundException,
    TransferLimitNotFoundException,
)
from app.models.enums import PrivilegeLevel
from app.repositories.transfer_limit_repository import TransferLimitRepository
from app.integration.account_service_client import account_service_client

logger = logging.getLogger(__name__)


class TransferLimitService:
    """Service for transfer limit operations."""

    def __init__(self, limit_repo: Optional[TransferLimitRepository] = None):
        """Initialize service with repositories."""
        self.limit_repo = limit_repo or TransferLimitRepository()
        self.account_client = account_service_client

    async def get_transfer_limit(self, account_number: int) -> Dict[str, Any]:
        """
        Get transfer limit details for an account.

        Returns privilege-based daily limit and remaining amount.

        Args:
            account_number: Account number

        Returns:
            Dict with:
            - privilege: PREMIUM/GOLD/SILVER/BASIC
            - daily_limit: Daily transfer limit in rupees
            - daily_used: Amount already transferred today
            - daily_remaining: daily_limit - daily_used
            - transaction_limit: Max transactions per day
            - transactions_today: Transactions made today
            - transactions_remaining: transaction_limit - transactions_today

        Raises:
            AccountNotFoundException: If account doesn't exist
            TransferLimitNotFoundException: If no limit found for privilege
        """
        logger.info(f"🔍 Getting transfer limits for account {account_number}")

        # STEP 1: Validate account exists and get privilege
        account_data = await self.account_client.validate_account(account_number)
        privilege = account_data.get("privilege", "BASIC")

        logger.info(f"📊 Account {account_number} privilege: {privilege}")

        # STEP 2: Get transfer limit rule for privilege
        limit_rule = await self.limit_repo.get_transfer_rule(privilege)

        if not limit_rule:
            raise TransferLimitNotFoundException(
                f"No transfer limit rule found for privilege {privilege}"
            )

        daily_limit = Decimal(str(limit_rule.get("daily_limit", 0)))
        transaction_limit = limit_rule.get("transaction_limit", 0)

        # STEP 3: Get daily usage for this account
        daily_used = await self.limit_repo.get_daily_used_amount(account_number)
        daily_remaining = max(Decimal(0), daily_limit - daily_used)

        daily_count = await self.limit_repo.get_daily_transaction_count(account_number)
        transactions_remaining = max(0, transaction_limit - daily_count)

        logger.info(
            f"✅ Transfer limits retrieved - Used: ₹{daily_used}, Remaining: ₹{daily_remaining}, "
            f"Txns: {daily_count}/{transaction_limit}"
        )

        return {
            "account_number": account_number,
            "privilege": privilege,
            "daily_limit": float(daily_limit),
            "daily_used": float(daily_used),
            "daily_remaining": float(daily_remaining),
            "transaction_limit": transaction_limit,
            "transactions_today": daily_count,
            "transactions_remaining": transactions_remaining,
        }

    async def get_remaining_limit(self, account_number: int) -> Dict[str, Any]:
        """
        Get remaining transfer limit (quick check).

        Args:
            account_number: Account number

        Returns:
            Dict with daily_remaining and transactions_remaining

        Raises:
            AccountNotFoundException: If account doesn't exist
            TransferLimitNotFoundException: If no limit found
        """
        logger.info(f"⚡ Quick check remaining limit for account {account_number}")

        # Get account privilege
        account_data = await self.account_client.validate_account(account_number)
        privilege = account_data.get("privilege", "BASIC")

        # Get limit rule
        limit_rule = await self.limit_repo.get_transfer_rule(privilege)

        if not limit_rule:
            raise TransferLimitNotFoundException(
                f"No transfer limit rule found for privilege {privilege}"
            )

        daily_limit = Decimal(str(limit_rule.get("daily_limit", 0)))
        transaction_limit = limit_rule.get("transaction_limit", 0)

        # Get daily usage
        daily_used = await self.limit_repo.get_daily_used_amount(account_number)
        daily_remaining = max(Decimal(0), daily_limit - daily_used)

        daily_count = await self.limit_repo.get_daily_transaction_count(account_number)
        transactions_remaining = max(0, transaction_limit - daily_count)

        return {
            "account_number": account_number,
            "daily_remaining": float(daily_remaining),
            "transactions_remaining": transactions_remaining,
        }

    async def get_all_transfer_rules(self) -> List[Dict[str, Any]]:
        """
        Get all transfer rules for all privilege levels.

        Used by admins to view or manage transfer limit policies.

        Returns:
            List of transfer rule dicts with:
            - privilege: PREMIUM/GOLD/SILVER/BASIC
            - daily_limit: Daily transfer limit in rupees
            - transaction_limit: Max transactions per day
            - created_at: When rule was created
        """
        logger.info("📋 Fetching all transfer limit rules")

        rules = []
        for privilege in [
            PrivilegeLevel.PREMIUM,
            PrivilegeLevel.GOLD,
            PrivilegeLevel.SILVER,
        ]:
            rule = await self.limit_repo.get_transfer_rule(privilege.value)
            if rule:
                rules.append(
                    {
                        "privilege": privilege.value,
                        "daily_limit": float(rule.get("daily_limit", 0)),
                        "transaction_limit": rule.get("transaction_limit", 0),
                        "created_at": rule.get("created_at", ""),
                    }
                )

        logger.info(f"✅ Retrieved {len(rules)} transfer limit rules")
        return rules

    async def update_transfer_rule(
        self, privilege: str, daily_limit: Decimal, transaction_limit: int
    ) -> Dict[str, Any]:
        """
        Update transfer limit rule for a privilege level.

        Admin operation to modify transfer policies.

        Args:
            privilege: PREMIUM/GOLD/SILVER/BASIC
            daily_limit: New daily transfer limit
            transaction_limit: New max transactions per day

        Returns:
            Updated rule dict

        Raises:
            InvalidPrivilegeException: If privilege is invalid
        """
        logger.info(
            f"🔧 Updating transfer rule for {privilege}: "
            f"₹{daily_limit}/day, {transaction_limit} txns/day"
        )

        # Validate privilege
        valid_privileges = [p.value for p in PrivilegeLevel]
        if privilege not in valid_privileges:
            raise ValueError(f"Invalid privilege level: {privilege}")

        # Update rule
        await self.limit_repo.create_transfer_rule(
            privilege=privilege, daily_limit=daily_limit, transaction_limit=transaction_limit
        )

        logger.info(f"✅ Transfer rule updated for {privilege}")

        return {
            "privilege": privilege,
            "daily_limit": float(daily_limit),
            "transaction_limit": transaction_limit,
        }

    async def check_can_transfer(
        self, account_number: int, proposed_amount: Decimal
    ) -> Dict[str, Any]:
        """
        Check if account can make a transfer of proposed amount.

        Quick validation before attempting transfer.

        Args:
            account_number: Account number
            proposed_amount: Amount to transfer

        Returns:
            Dict with:
            - can_transfer: True/False
            - reason: Why transfer is blocked (if can_transfer=False)
            - daily_remaining: After this transfer

        Raises:
            AccountNotFoundException: If account doesn't exist
        """
        logger.info(f"❓ Checking if account {account_number} can transfer ₹{proposed_amount}")

        # Get limits
        limit_data = await self.get_transfer_limit(account_number)

        daily_remaining = Decimal(str(limit_data["daily_remaining"]))
        transactions_remaining = limit_data["transactions_remaining"]

        # Check amount limit
        if proposed_amount > daily_remaining:
            reason = (
                f"Daily limit exceeded. Remaining: ₹{daily_remaining}, "
                f"Requested: ₹{proposed_amount}"
            )
            logger.warning(f"❌ {reason}")
            return {
                "can_transfer": False,
                "reason": reason,
                "daily_remaining": float(daily_remaining),
            }

        # Check transaction count limit
        if transactions_remaining <= 0:
            reason = "Daily transaction limit reached"
            logger.warning(f"❌ {reason}")
            return {
                "can_transfer": False,
                "reason": reason,
                "transactions_remaining": transactions_remaining,
            }

        new_remaining = daily_remaining - proposed_amount

        logger.info(f"✅ Transfer allowed. Remaining after: ₹{new_remaining}")

        return {
            "can_transfer": True,
            "daily_remaining": float(new_remaining),
            "transactions_remaining": transactions_remaining - 1,
        }


# Singleton instance
transfer_limit_service = TransferLimitService()
