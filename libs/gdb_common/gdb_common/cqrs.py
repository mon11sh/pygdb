"""
CQRS — Command Query Responsibility Segregation.

Commands change state; queries only read it. Splitting them into two buses makes
the write path and the read path explicit, independently testable, and
independently optimizable (e.g. a read replica / denormalized read model later).

    commands = CommandBus(); queries = QueryBus()
    commands.register(DepositCommand, deposit_handler)
    queries.register(GetBalanceQuery, balance_handler)
    await commands.dispatch(DepositCommand(...))   # write
    await queries.dispatch(GetBalanceQuery(...))    # read
"""

from __future__ import annotations

from typing import Awaitable, Callable, Dict, Type, TypeVar


class Command:
    """Marker base for state-changing messages."""


class Query:
    """Marker base for read-only messages."""


class NoHandlerError(Exception):
    """Raised by a bus when no handler is registered for a dispatched message."""

    def __init__(self, message_type: type):
        """Record the unhandled message type on the exception.

        Args:
            message_type: The command/query class that had no registered handler.
        """
        super().__init__(f"No handler registered for {message_type.__name__}")
        self.message_type = message_type


M = TypeVar("M")
Handler = Callable[[object], Awaitable[object]]


class _Bus:
    """Shared message-bus machinery for the command and query buses.

    Maintains a registry of message-type -> handler and dispatches an incoming
    message to the handler registered for its exact type. Subclasses set `_base`
    to restrict which message types the bus accepts.
    """

    _base: type = object
    _label: str = "message"

    def __init__(self):
        """Initialize an empty message-type -> handler registry."""
        self._handlers: Dict[type, Handler] = {}

    def register(self, message_type: type, handler: Handler) -> Handler:
        """Register a handler for a message type.

        Args:
            message_type: The command/query class to handle; must be a subclass
                of this bus's `_base`.
            handler: Async callable invoked with a message of that type.

        Returns:
            The handler, so this may be used directly or as a decorator.

        Raises:
            TypeError: If message_type is not a subclass of the bus's base type.
        """
        if not (isinstance(message_type, type) and issubclass(message_type, self._base)):
            raise TypeError(
                f"{type(self).__name__} only accepts {self._base.__name__} types, got {message_type!r}"
            )
        self._handlers[message_type] = handler
        return handler

    def handler(self, message_type: type):
        """Decorator form: @bus.handler(SomeCommand)."""
        def _decorator(fn: Handler) -> Handler:
            """Register ``fn`` as the handler for the message type and return it."""
            self.register(message_type, fn)
            return fn
        return _decorator

    async def dispatch(self, message: object):
        """Route a message to its registered handler and return the result.

        Args:
            message: A command/query instance whose exact type is looked up.

        Returns:
            The awaited result of the matching handler.

        Raises:
            NoHandlerError: If no handler is registered for the message's type.
        """
        handler = self._handlers.get(type(message))
        if handler is None:
            raise NoHandlerError(type(message))
        return await handler(message)


class CommandBus(_Bus):
    """Bus for state-changing commands (accepts only `Command` subclasses)."""

    _base = Command
    _label = "command"


class QueryBus(_Bus):
    """Bus for read-only queries (accepts only `Query` subclasses)."""

    _base = Query
    _label = "query"
