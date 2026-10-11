"""CQRS bus tests (gdb_common.cqrs)."""

import pytest

from gdb_common.cqrs import CommandBus, QueryBus, Command, Query, NoHandlerError


class DoThing(Command):
    def __init__(self, x):
        self.x = x


class AskThing(Query):
    def __init__(self, x):
        self.x = x


@pytest.mark.asyncio
async def test_command_bus_dispatches_to_handler():
    bus = CommandBus()

    async def handle(cmd):
        return cmd.x * 2

    bus.register(DoThing, handle)
    assert await bus.dispatch(DoThing(21)) == 42


@pytest.mark.asyncio
async def test_query_bus_dispatches_to_handler():
    bus = QueryBus()
    bus.register(AskThing, lambda q: _async(q.x + 1))
    assert await bus.dispatch(AskThing(9)) == 10


@pytest.mark.asyncio
async def test_unregistered_message_raises_no_handler():
    bus = CommandBus()
    with pytest.raises(NoHandlerError):
        await bus.dispatch(DoThing(1))


def test_command_bus_rejects_query_types():
    # Separation is enforced: a Query cannot be registered on the CommandBus.
    with pytest.raises(TypeError):
        CommandBus().register(AskThing, lambda q: None)


def test_query_bus_rejects_command_types():
    with pytest.raises(TypeError):
        QueryBus().register(DoThing, lambda c: None)


@pytest.mark.asyncio
async def test_decorator_registration():
    bus = QueryBus()

    @bus.handler(AskThing)
    async def _h(q):
        return "ok"

    assert await bus.dispatch(AskThing(0)) == "ok"


async def _async(v):
    return v
