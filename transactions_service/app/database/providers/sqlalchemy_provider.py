"""
SQLAlchemy provider — serves sqlite / mysql. (Postgres/supabase keep the existing
asyncpg path via AsyncpgProvider so current behaviour/tests are unchanged.)

Responsibilities:
  - best-effort create the target database (mysql) so the "just works" experience
    is preserved; no-op for sqlite (file auto-created).
  - build the async engine + session factory.
  - create tables via Base.metadata.create_all (portable across dialects).
  - seed transfer_limits + minimal sample logs if empty (reusing the repos).

All SQLAlchemy imports are inside methods so this module is only "heavy" when a
SQL provider is actually initialized.
"""

import logging

from .base import DatabaseProvider

logger = logging.getLogger(__name__)


class SqlAlchemyProvider(DatabaseProvider):
    """Database provider backed by SQLAlchemy async engine (sqlite/mysql).

    Owns the async engine and session factory, creates schema and seed data on
    init, and exposes the SQLAlchemy repository implementations. Postgres/supabase
    continue to use AsyncpgProvider; this provider serves the remaining SQL dialects.
    """

    def __init__(self, url: str, name: str):
        """Store the connection URL and dialect name; defer engine/repo creation to init.

        Args:
            url: SQLAlchemy async connection URL.
            name: Dialect name (e.g. "sqlite", "mysql") used for engine tuning.
        """
        self.name = name
        self._url = url
        self._engine = None
        self._session_factory = None
        self._txn_repo = None
        self._log_repo = None
        self._limit_repo = None
        self._idem_repo = None

    async def init(self) -> None:
        """Create the database, engine, tables, repositories, and seed data.

        Best-effort creates the target database, builds the async engine and
        session factory (with dialect-specific pooling), creates all tables via
        the ORM metadata, instantiates the four SQLAlchemy repositories, and seeds
        transfer limits plus sample logs when the log table is empty.
        """
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

        from ..orm_models import Base
        from ..seed_data import seed_transfer_limits, seed_sample_logs
        from ...repositories.sqlalchemy_repositories import (
            SqlAlchemyTransactionRepository,
            SqlAlchemyTransactionLogRepository,
            SqlAlchemyTransferLimitRepository,
            SqlAlchemyIdempotencyRepository,
        )

        await self._ensure_database()
        logger.info(f"🗄️  Database provider: SQL '{self.name}' → {self._safe_url()}")

        # SQLAlchemy 2.0.23 + aiomysql: pool_pre_ping is broken (ping() arg
        # mismatch), so recycle connections for MySQL and pre-ping the rest.
        engine_kwargs = {"future": True}
        if self.name == "mysql":
            engine_kwargs["pool_recycle"] = 3600
        else:
            engine_kwargs["pool_pre_ping"] = True
        self._engine = create_async_engine(self._url, **engine_kwargs)
        self._session_factory = async_sessionmaker(self._engine, expire_on_commit=False)

        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        self._txn_repo = SqlAlchemyTransactionRepository(self._session_factory)
        self._log_repo = SqlAlchemyTransactionLogRepository(self._session_factory)
        self._limit_repo = SqlAlchemyTransferLimitRepository(self._session_factory)
        self._idem_repo = SqlAlchemyIdempotencyRepository(self._session_factory)

        # Seed transfer limits (idempotent upsert) + sample logs if empty.
        await seed_transfer_limits(self._limit_repo)
        existing, _ = await self._log_repo.get_account_logs(account_number=1001, limit=1)
        if not existing:
            await seed_sample_logs(self._txn_repo, self._log_repo)
            logger.info("🌱 Seeded transfer limits + sample logs.")

    async def _ensure_database(self) -> None:
        """Best-effort create the target DB for mysql if it's missing (no-op sqlite)."""
        try:
            from sqlalchemy.engine import make_url

            url = make_url(self._url)
            backend = url.get_backend_name()  # 'sqlite' | 'mysql' | 'postgresql'
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
            logger.warning(f"ensure_database skipped ({self.name}): {e}")

    def _safe_url(self) -> str:
        """Return the connection URL with the password masked, for safe logging."""
        from sqlalchemy.engine import make_url
        u = make_url(self._url)
        return str(u.set(password="***")) if u.password else str(u)

    async def dispose(self) -> None:
        """Dispose of the async engine and release its connection pool."""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None

    def transaction_repository(self):
        """Return the SQLAlchemy transaction repository instance."""
        return self._txn_repo

    def transaction_log_repository(self):
        """Return the SQLAlchemy transaction log repository instance."""
        return self._log_repo

    def transfer_limit_repository(self):
        """Return the SQLAlchemy transfer limit repository instance."""
        return self._limit_repo

    def idempotency_repository(self):
        """Return the SQLAlchemy idempotency repository instance."""
        return self._idem_repo
