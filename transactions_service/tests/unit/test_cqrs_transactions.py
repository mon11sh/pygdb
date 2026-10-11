"""CQRS wiring tests for the transactions domain (build_transaction_buses)."""

import pytest

from gdb_common.cqrs import NoHandlerError
from app.cqrs import (
    build_transaction_buses,
    DepositCommand,
    TransferCommand,
    GetTransferLimitQuery,
    GetAllTransferRulesQuery,
)


class _FakeDeposit:
    def __init__(self):
        self.called_with = None

    async def process_deposit(self, account_number, amount, description, idempotency_key):
        self.called_with = (account_number, amount, description, idempotency_key)
        return {"status": "success", "account_number": account_number, "amount": amount}


class _FakeLimits:
    async def get_transfer_limit(self, account_number):
        return {"account_number": account_number, "daily_remaining": 50000.0}

    async def get_all_transfer_rules(self):
        return [{"privilege": "GOLD"}]


@pytest.mark.asyncio
async def test_command_dispatch_delegates_to_service():
    deposit = _FakeDeposit()
    commands, _ = build_transaction_buses(deposit=deposit, withdraw=object(),
                                          transfer=object(), limits=_FakeLimits())
    result = await commands.dispatch(DepositCommand(account_number=101, amount=500))
    assert result["status"] == "success"
    assert deposit.called_with == (101, 500, None, None)


@pytest.mark.asyncio
async def test_query_dispatch_delegates_to_service():
    _, queries = build_transaction_buses(deposit=object(), withdraw=object(),
                                         transfer=object(), limits=_FakeLimits())
    limit = await queries.dispatch(GetTransferLimitQuery(account_number=202))
    assert limit["daily_remaining"] == 50000.0
    rules = await queries.dispatch(GetAllTransferRulesQuery())
    assert rules == [{"privilege": "GOLD"}]


@pytest.mark.asyncio
async def test_command_not_accepted_on_query_bus():
    # A write command has no query handler -> segregation holds.
    _, queries = build_transaction_buses(deposit=object(), withdraw=object(),
                                         transfer=object(), limits=_FakeLimits())
    with pytest.raises(NoHandlerError):
        await queries.dispatch(TransferCommand(from_account=1, to_account=2, amount=10, pin="1234"))
