"""
Accounts Service - Database bootstrap entry points (provider-agnostic).

This module preserves the exact symbol names that `app/main.py` imports
(`initialize_db`, `close_db`) while delegating all real work to the runtime
database provider selected by settings.DATABASE_PROVIDER (sqlite / mysql /
postgres / supabase / inmemory). See `app/database/connection.py` and
`app/database/providers/`.

Switch databases by changing ONLY settings.DATABASE_PROVIDER (+ DATABASE_URL).
Same source, five databases.
"""

import logging

from .connection import init_db, close_db, get_provider

logger = logging.getLogger(__name__)


async def initialize_db(database_url: str = None, min_size: int = 5, max_size: int = 20):
    """Initialize the active database provider (schema + seed).

    The legacy `database_url` / pool-size arguments are accepted for backward
    compatibility with the FastAPI lifespan call in main.py, but the concrete
    connection URL now comes from settings via the provider factory.
    """
    await init_db()
    logger.info("✅ Database initialized via provider")
    return get_provider()


def get_account_repository():
    """Return the active AccountRepository from the current provider."""
    return get_provider().account_repository()


__all__ = ["initialize_db", "close_db", "get_provider", "get_account_repository"]
