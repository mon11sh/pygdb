"""
User Management Service - Database bootstrap (provider-agnostic).

The concrete database is chosen at runtime from settings.DATABASE_PROVIDER via
the provider factory (sqlite / mysql / postgres / supabase / inmemory). The rest
of the application only ever talks to the provider's repositories, never to a
specific database.

`init_db()` / `close_db()` are invoked by the FastAPI lifespan in main.py.
The provider (and therefore SQLAlchemy, for SQL providers) is created lazily on
first use, so importing this module has no heavy dependencies.
"""

import logging
from typing import Optional

from .providers.base import DatabaseProvider

logger = logging.getLogger(__name__)

_provider: Optional[DatabaseProvider] = None


def get_provider() -> DatabaseProvider:
    """Return the active database provider, creating it on first use."""
    global _provider
    if _provider is None:
        from .providers.factory import create_provider
        _provider = create_provider()
    return _provider


async def init_db() -> None:
    """Initialize the selected database provider (schema + seed)."""
    await get_provider().init()


async def close_db() -> None:
    """Dispose the active database provider."""
    global _provider
    if _provider is not None:
        await _provider.dispose()
        _provider = None
        logger.info("✅ Database provider disposed")
