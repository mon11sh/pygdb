"""CQRS layer for the transactions domain.

The write path (money movement) and the read path (limits / history) are modelled
as separate Command and Query messages, dispatched through two independent buses
(`gdb_common.cqrs`). Handlers delegate to the existing service singletons, so the
CQRS layer adds explicit read/write segregation without duplicating business logic.
"""

from .messages import (
    DepositCommand,
    WithdrawCommand,
    TransferCommand,
    GetTransferLimitQuery,
    GetAllTransferRulesQuery,
)
from .buses import build_transaction_buses

__all__ = [
    "DepositCommand",
    "WithdrawCommand",
    "TransferCommand",
    "GetTransferLimitQuery",
    "GetAllTransferRulesQuery",
    "build_transaction_buses",
]
