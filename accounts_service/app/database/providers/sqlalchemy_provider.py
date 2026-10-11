"""
SQLAlchemy provider — one implementation that serves sqlite / mysql / postgres /
supabase. Supabase simply reuses the PostgreSQL path (it *is* PostgreSQL).

Responsibilities:
  - best-effort create the target database (postgres/mysql) so the current
    "just works" experience is preserved; no-op for sqlite (file auto-created).
  - build the async engine + session factory.
  - create tables via Base.metadata.create_all (portable across dialects).
  - seed default accounts if empty (reusing the repository, no duplicated SQL).

All SQLAlchemy imports are inside methods so this module is only "heavy" when a
SQL provider is actually initialized.
"""

import logging

from .base import DatabaseProvider

logger = logging.getLogger(__name__)


class SqlAlchemyProvider(DatabaseProvider):
    """DatabaseProvider serving every SQL backend (sqlite / mysql / postgres / supabase).

    Owns the async SQLAlchemy engine and session factory and exposes a single
    ``SqlAlchemyAccountRepository``. The concrete dialect is selected purely by
    the connection URL; Supabase reuses the PostgreSQL path. Engine and imports
    are created lazily in :meth:`init` so importing the module stays cheap.
    """

    def __init__(self, url: str, name: str):
        """Store the connection URL and provider name; defer engine creation to init().

        Args:
            url: Async SQLAlchemy connection URL for the target database.
            name: Provider name (e.g. ``sqlite``/``mysql``/``postgres``/``supabase``),
                used to drive dialect-specific behaviour.
        """
        self.name = name
        self._url = url
        self._engine = None
        self._session_factory = None
        self._account_repo = None

    async def init(self) -> None:
        """Provision the backend: ensure the DB, build the engine, create tables, seed.

        Best-effort creates the target database (except Supabase), constructs the
        async engine and session factory with dialect-appropriate pooling, runs
        ``Base.metadata.create_all``, wires up the repository, and seeds the
        default accounts when the table is empty.
        """
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

        from app.database.orm_models import Base
        from app.database.seed_data import seed_default_accounts
        from app.repositories.sqlalchemy_repositories import SqlAlchemyAccountRepository

        # Supabase gives you a single ready-made `postgres` database and REQUIRES
        # SSL — so skip the CREATE DATABASE probe and turn SSL on for it.
        if self.name != "supabase":
            await self._ensure_database()
        connect_args = {"ssl": "require"} if self.name == "supabase" else {}
        logger.info(f"🗄️  Database provider: SQL '{self.name}' → {self._safe_url()}")

        # SQLAlchemy 2.0.23 + aiomysql: pool_pre_ping is broken (ping() arg
        # mismatch), so recycle connections for MySQL and pre-ping the rest.
        engine_kwargs = {"future": True, "connect_args": connect_args}
        if self.name == "mysql":
            engine_kwargs["pool_recycle"] = 3600
        else:
            engine_kwargs["pool_pre_ping"] = True
        self._engine = create_async_engine(self._url, **engine_kwargs)
        self._session_factory = async_sessionmaker(self._engine, expire_on_commit=False)

        # Create tables (portable). Does NOT create the database itself.
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        self._account_repo = SqlAlchemyAccountRepository(self._session_factory)

        if not await self._account_repo.get_all_accounts():
            count = await seed_default_accounts(self._account_repo)
            logger.info(f"🌱 Seeded {count} default accounts.")

    async def _ensure_database(self) -> None:
        """Best-effort create the target DB for postgres/mysql if it's missing."""
        try:
            from sqlalchemy.engine import make_url

            url = make_url(self._url)
            backend = url.get_backend_name()  # 'postgresql' | 'mysql' | 'sqlite'
            if backend == "sqlite" or not url.database:
                return

            if backend == "postgresql":
                import asyncpg
                conn = await asyncpg.connect(
                    host=url.host, port=url.port or 5432,
                    user=url.username, password=url.password, database="postgres",
                )
                try:
                    exists = await conn.fetchval(
                        "SELECT 1 FROM pg_database WHERE datname = $1", url.database
                    )
                    if not exists:
                        await conn.execute(f'CREATE DATABASE "{url.database}"')
                        logger.info(f"📦 Created database: {url.database}")
                finally:
                    await conn.close()

            elif backend == "mysql":
                import aiomysql
                conn = await aiomysql.connect(
                    host=url.host, port=url.port or 3306,
                    user=url.username, password=url.password or "",
                )
                try:
                    async with conn.cursor() as cur:
                        await cur.execute(
                            f"CREATE DATABASE IF NOT EXISTS `{url.database}`"
                        )
                finally:
                    conn.close()
        except Exception as e:
            # Non-fatal: if the DB already exists or the account lacks CREATE
            # rights (e.g. Supabase), we continue and let create_all run.
            logger.warning(f"ensure_database skipped ({self.name}): {e}")

    def _safe_url(self) -> str:
        """Return the connection URL with any password masked, safe for logging."""
        from sqlalchemy.engine import make_url
        u = make_url(self._url)
        return str(u.set(password="***")) if u.password else str(u)

    async def dispose(self) -> None:
        """Dispose the async engine and its connection pool, if one was created."""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None

    def account_repository(self):
        """Return the SQLAlchemy-backed AccountRepository (available after init())."""
        return self._account_repo
