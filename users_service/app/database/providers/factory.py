"""
Database provider factory.

    settings.DATABASE_PROVIDER  →  create_provider()  →  concrete DatabaseProvider

Also resolves the SQLAlchemy connection URL for the SQL providers, coercing any
plain/sync URL to its async driver so the same DATABASE_URL a student pastes
(e.g. postgresql://…, mysql+pymysql://…) works with the async engine.
"""

from .base import DatabaseProvider
from ...config.settings import settings


# Map a plain/sync URL scheme to the async driver we actually use.
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
    return r  # already async: postgresql+asyncpg / mysql+aiomysql / sqlite+aiosqlite


def resolve_database_url(provider: str) -> str:
    """Build the async SQLAlchemy URL for a SQL provider."""
    explicit = (settings.DATABASE_URL or "").strip()
    if explicit:
        return _to_async_url(explicit)

    if provider in ("postgres", "supabase"):
        pw = settings.DATABASE_PASSWORD
        auth = f"{settings.DATABASE_USER}:{pw}@" if pw else f"{settings.DATABASE_USER}@"
        return (
            f"postgresql+asyncpg://{auth}"
            f"{settings.DATABASE_HOST}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}"
        )

    if provider == "mysql":
        pw = settings.DATABASE_PASSWORD
        auth = f"{settings.DATABASE_USER}:{pw}@" if pw else f"{settings.DATABASE_USER}@"
        # DATABASE_PORT defaults to 5432 (postgres); use MySQL's 3306 unless overridden.
        port = settings.DATABASE_PORT if settings.DATABASE_PORT != 5432 else 3306
        return (
            f"mysql+aiomysql://{auth}"
            f"{settings.DATABASE_HOST}:{port}/{settings.DATABASE_NAME}"
        )

    if provider == "sqlite":
        # File-based, relative to the service working directory. No server needed.
        return "sqlite+aiosqlite:///./gdb_users.db"

    raise ValueError(f"No URL rule for provider '{provider}'")


def create_provider() -> DatabaseProvider:
    """Instantiate the provider chosen by settings.DATABASE_PROVIDER."""
    provider = (settings.DATABASE_PROVIDER or "postgres").strip().lower()

    if provider == "inmemory":
        from .inmemory_provider import InMemoryProvider
        return InMemoryProvider()

    if provider in ("sqlite", "mysql", "postgres", "supabase"):
        from .sqlalchemy_provider import SqlAlchemyProvider
        return SqlAlchemyProvider(resolve_database_url(provider), name=provider)

    raise ValueError(
        f"Unsupported DATABASE_PROVIDER '{provider}'. "
        "Use one of: sqlite, mysql, postgres, supabase, inmemory."
    )
