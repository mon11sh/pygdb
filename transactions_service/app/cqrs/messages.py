"""Command and Query messages for the transactions domain.

Commands mutate state (money movement); queries are read-only. Field names mirror
the underlying service method parameters so handlers can unpack them directly.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from gdb_common.cqrs import Command, Query

from app.models.enums import TransferMode


# --------------------------------------------------------------------------- #
# Commands (write side)                                                        #
# --------------------------------------------------------------------------- #
@dataclass
class DepositCommand(Command):
    """Command to credit funds into an account, optionally idempotency-guarded."""
    account_number: int
    amount: Decimal
    description: Optional[str] = None
    idempotency_key: Optional[str] = None


@dataclass
class WithdrawCommand(Command):
    """Command to debit funds from an account; requires PIN verification."""
    account_number: int
    amount: Decimal
    pin: str
    description: Optional[str] = None
    idempotency_key: Optional[str] = None


@dataclass
class TransferCommand(Command):
    """Command to move funds between two accounts via a given transfer mode."""
    from_account: int
    to_account: int
    amount: Decimal
    pin: str
    transfer_mode: TransferMode = TransferMode.NEFT
    description: Optional[str] = None
    idempotency_key: Optional[str] = None


# --------------------------------------------------------------------------- #
# Queries (read side)                                                          #
# --------------------------------------------------------------------------- #
@dataclass
class GetTransferLimitQuery(Query):
    """Query for the transfer limit rule applicable to a single account."""
    account_number: int


@dataclass
class GetAllTransferRulesQuery(Query):
    """Query for the complete set of configured transfer limit rules."""
    pass
