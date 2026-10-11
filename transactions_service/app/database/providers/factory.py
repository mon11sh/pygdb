"""
Database provider factory.

    settings.DATABASE_PROVIDER  →  create_provider()  →  concrete DatabaseProvider

Also resolves the SQLAlchemy connection URL for the sqlite/mysql providers,
coercing any plain/sync URL to its async driver so a DATABASE_URL a student
pastes (e.g. mysql+pymysql://…) works with the async engine.

  - postgres / supabase → AsyncpgProvider (existing asyncpg path, unchanged)
  - sqlite / mysql      → SqlAlchemyProvider (portable SQLAlchemy)
  - inmemory            → InMemoryProvider (dict repos, no server)
"""

from .base import DatabaseProvider
from ...config.settings import settings


_ASYNC_SCHEMES = [
    ("postgresql+psycopg2://", "postgresql+asyncpg://"),
    ("postgresql+psycopg://", "postgresql+asyncpg://"),
    ("postgres://", "postgresql+asyncpg://"),
    ("postgresql://", "postgresql+asyncpg://"),
    ("mysql+pymysql://", "mysql+aiomysql://"),
    ("mysql://", "mysql+aiomysql://"),
    ("sqlite://", "sqlite+aiosqlite://"),
]


def _to_async_url(raw: str) -> str:
    """Coerce a URL to its async driver (leaves already-async URLs untouched)."""
    r = raw.strip()
    for old, new in _ASYNC_SCHEMES:
        if r.startswith(old):
            return new + r[len(old):]
    return r


def resolve_database_url(provider: str) -> str:
    """Build the async SQLAlchemy URL for a SQL provider."""
    explicit = (settings.DATABASE_URL or "").strip()
    if explicit:
        return _to_async_url(explicit)

    if provider in ("postgres", "supabase"):
        pw = settings.DB_PASSWORD
        auth = f"{settings.DB_USER}:{pw}@" if pw else f"{settings.DB_USER}@"
        return (
            f"postgresql+asyncpg://{auth}"
            f"{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        )

    if provider == "mysql":
        pw = settings.DB_PASSWORD
        auth = f"{settings.DB_USER}:{pw}@" if pw else f"{settings.DB_USER}@"
        # DB_PORT defaults to 5432 (postgres); use MySQL's 3306 unless overridden.
        port = settings.DB_PORT if settings.DB_PORT != 5432 else 3306
        return f"mysql+aiomysql://{auth}{settings.DB_HOST}:{port}/{settings.DB_NAME}"

    if provider == "sqlite":
        return "sqlite+aiosqlite:///./gdb_transactions.db"

    raise ValueError(f"No URL rule for provider '{provider}'")


def create_provider() -> DatabaseProvider:
    """Instantiate the provider chosen by settings.DATABASE_PROVIDER."""
    provider = (settings.DATABASE_PROVIDER or "postgres").strip().lower()

    if provider == "inmemory":
        from .inmemory_provider import InMemoryProvider
        return InMemoryProvider()

    if provider in ("postgres", "supabase"):
        from .asyncpg_provider import AsyncpgProvider
        return AsyncpgProvider(name=provider)

    if provider in ("sqlite", "mysql"):
        from .sqlalchemy_provider import SqlAlchemyProvider
        return SqlAlchemyProvider(resolve_database_url(provider), name=provider)

    raise ValueError(
        f"Unsupported DATABASE_PROVIDER '{provider}'. "
        "Use one of: sqlite, mysql, postgres, supabase, inmemory."
    )
