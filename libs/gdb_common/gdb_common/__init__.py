"""GDB shared internal utilities."""

from .observability import (
    correlation_id_ctx,
    current_correlation_id,
    new_correlation_id,
    install_observability,
    configure_json_logging,
)
from .internal_auth import make_internal_api_key_verifier
from .resilience import CircuitBreaker, BreakerState, CircuitBreakerOpen
from .discovery import ServiceRegistry, StaticResolver, create_registry_app
from .cqrs import CommandBus, QueryBus, Command, Query, NoHandlerError
from .ratelimit import RateLimiter

__all__ = [
    "RateLimiter",
    "ServiceRegistry",
    "StaticResolver",
    "create_registry_app",
    "CommandBus",
    "QueryBus",
    "Command",
    "Query",
    "NoHandlerError",
    "correlation_id_ctx",
    "current_correlation_id",
    "new_correlation_id",
    "install_observability",
    "configure_json_logging",
    "make_internal_api_key_verifier",
    "CircuitBreaker",
    "BreakerState",
    "CircuitBreakerOpen",
]
