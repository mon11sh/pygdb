"""Wire the transactions Command/Query buses to the existing service singletons.

`build_transaction_buses()` returns a (command_bus, query_bus) pair with all
handlers registered. Services are injectable so tests can pass fakes; by default
the production singletons are used.
"""

from gdb_common.cqrs import CommandBus, QueryBus

from app.cqrs.messages import (
    DepositCommand,
    WithdrawCommand,
    TransferCommand,
    GetTransferLimitQuery,
    GetAllTransferRulesQuery,
)


def build_transaction_buses(deposit=None, withdraw=None, transfer=None, limits=None):
    """Build and populate the command and query buses.

    Args are the four collaborating services; when omitted the module singletons
    are imported lazily (keeps import time cheap and avoids import cycles).
    """
    if deposit is None:
        from app.services.deposit_service import deposit_service as deposit
    if withdraw is None:
        from app.services.withdraw_service import withdraw_service as withdraw
    if transfer is None:
        from app.services.transfer_service import transfer_service as transfer
    if limits is None:
        from app.services.transfer_limit_service import transfer_limit_service as limits

    commands = CommandBus()
    queries = QueryBus()

    # --- write side -------------------------------------------------------- #
    commands.register(
        DepositCommand,
        lambda c: deposit.process_deposit(
            c.account_number, c.amount, c.description, c.idempotency_key
        ),
    )
    commands.register(
        WithdrawCommand,
        lambda c: withdraw.process_withdraw(
            c.account_number, c.amount, c.pin, c.description, c.idempotency_key
        ),
    )
    commands.register(
        TransferCommand,
        lambda c: transfer.process_transfer(
            c.from_account, c.to_account, c.amount, c.pin,
            c.transfer_mode, c.description, c.idempotency_key,
        ),
    )

    # --- read side --------------------------------------------------------- #
    queries.register(
        GetTransferLimitQuery,
        lambda q: limits.get_transfer_limit(q.account_number),
    )
    queries.register(
        GetAllTransferRulesQuery,
        lambda q: limits.get_all_transfer_rules(),
    )

    return commands, queries
