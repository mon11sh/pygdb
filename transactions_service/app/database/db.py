"""
Database bootstrap (provider-agnostic).

The concrete database is chosen at runtime from settings.DATABASE_PROVIDER via
the provider factory (sqlite / mysql / postgres / supabase / inmemory). The rest
of the application only ever talks to the provider's repositories.

Backwards compatibility:
  - `database` (DatabaseConnection singleton) is preserved because the raw-asyncpg
    repositories and several tests reference it (`app.repositories.*.database`).
    For the postgres/supabase provider these repos talk to this shared pool.
  - `database.initialize()` / `database.close()` are preserved (imported by
    app/main.py) and now delegate to the active provider (init/dispose).

The provider (and therefore SQLAlchemy, for the SQL providers) is created lazily
on first use, so importing this module stays light.
"""

import asyncpg
from typing import Optional
from app.config.settings import settings
import logging

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Provider lifecycle (the new abstraction main.py / DI depend on)
# --------------------------------------------------------------------------- #

_provider = None


def get_provider():
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


class DatabaseConnection:
    """PostgreSQL connection pool manager (asyncpg path for postgres/supabase).

    Also exposes the provider-aware `initialize()` / `close()` entrypoints that
    app/main.py calls, delegating to the active provider.
    """

    _pool: Optional[asyncpg.Pool] = None

    # ---- provider-aware entrypoints (used by app/main.py) ----------------- #

    @classmethod
    async def initialize(cls):
        """Initialize the active database provider (postgres/supabase/sqlite/
        mysql/inmemory). Returns the asyncpg pool when the postgres path is
        active, otherwise None."""
        await init_db()
        return cls._pool

    @classmethod
    async def close(cls) -> None:
        """Dispose the active provider (and close the asyncpg pool if open)."""
        await close_db()

    # ---- asyncpg pool bootstrap (postgres / supabase) --------------------- #

    @classmethod
    async def bootstrap_asyncpg(cls) -> asyncpg.Pool:
        """Create the pool, run the schema and seed transfer_limits + sample
        logs. Preserves the original 'just works' postgres experience."""
        if cls._pool is not None:
            return cls._pool

        # Supabase requires SSL; enable it only for the supabase provider.
        ssl_mode = "require" if settings.DATABASE_PROVIDER.strip().lower() == "supabase" else None

        # 1. Connect to postgres DB to verify/create target DB
        try:
            logger.info(f"Checking if database {settings.DB_NAME} exists...")
            temp_conn = await asyncpg.connect(
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                database="postgres",
                ssl=ssl_mode,
            )
            db_exists = await temp_conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1",
                settings.DB_NAME
            )
            if not db_exists:
                logger.info(f"📦 Creating database: {settings.DB_NAME}")
                await temp_conn.execute(f"CREATE DATABASE {settings.DB_NAME}")
                logger.info(f"✅ Database created: {settings.DB_NAME}")
            else:
                logger.info(f"✅ Database already exists: {settings.DB_NAME}")
            await temp_conn.close()
        except Exception as e:
            logger.error(f"⚠️ Error verifying/creating database {settings.DB_NAME}: {e}")

        # 2. Connect pool
        try:
            cls._pool = await asyncpg.create_pool(
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                database=settings.DB_NAME,
                min_size=settings.DB_POOL_MIN_SIZE,
                max_size=settings.DB_POOL_MAX_SIZE,
                command_timeout=settings.DB_TIMEOUT,
                ssl=ssl_mode,
            )
            logger.info("✅ Database connection pool initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize database pool: {str(e)}")
            raise ConnectionError(f"Database connection failed: {str(e)}")

        # 3. Check if tables exist, run schema, and seed
        try:
            from pathlib import Path
            async with cls._pool.acquire() as conn:
                limits_exists = await conn.fetchval(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'transfer_limits')"
                )
                if not limits_exists:
                    logger.info("📋 Core table 'transfer_limits' does not exist. Running transactions_schema.sql...")
                    schema_path = Path(__file__).parent / "transactions_schema.sql"
                    if schema_path.exists():
                        with open(schema_path, "r", encoding="utf-8") as f:
                            schema_sql = f.read()
                        await conn.execute(schema_sql)
                        logger.info("✅ Schema executed successfully")
                    else:
                        logger.error(f"❌ Schema file not found at {schema_path}")

                # Check limits count and seed transfer limits
                limits_count = await conn.fetchval("SELECT COUNT(*) FROM transfer_limits")
                if limits_count == 0:
                    logger.info("🌱 Seeding transfer limits...")
                    await conn.execute(
                        """
                        INSERT INTO transfer_limits (privilege, daily_limit, per_transaction_limit)
                        VALUES
                            ('PREMIUM', 100000.00, 50000.00),
                            ('GOLD', 50000.00, 25000.00),
                            ('SILVER', 25000.00, 12500.00)
                        """
                    )
                    logger.info("✅ Seeded transfer limits")

                # Check transaction logs count and seed dummy logs
                logs_count = await conn.fetchval("SELECT COUNT(*) FROM transaction_logging")
                if logs_count == 0:
                    logger.info("🌱 Seeding dummy transaction logs...")

                    # Deposit to 1001 (John Doe)
                    await conn.execute(
                        """
                        INSERT INTO transaction_logging (account_number, amount, transaction_type, reference_id, description, mode, status)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                        """,
                        1001, 60000.00, "DEPOSIT", None, "Initial deposit", "CASH", "SUCCESS"
                    )

                    # Transfer from 1002 (Admin) to 1001 (John Doe)
                    await conn.execute(
                        """
                        INSERT INTO fund_transfers (from_account, to_account, transfer_amount, transfer_mode)
                        VALUES ($1, $2, $3, $4)
                        """,
                        1002, 1001, 10000.00, "IMPS"
                    )

                    # Debit log for 1002
                    await conn.execute(
                        """
                        INSERT INTO transaction_logging (account_number, amount, transaction_type, reference_id, description, mode, status)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                        """,
                        1002, 10000.00, "TRANSFER", 1, "Fund Transfer to 1001", "IMPS", "SUCCESS"
                    )

                    # Credit log for 1001
                    await conn.execute(
                        """
                        INSERT INTO transaction_logging (account_number, amount, transaction_type, reference_id, description, mode, status)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                        """,
                        1001, 10000.00, "TRANSFER", 1, "Fund Transfer from 1002", "IMPS", "SUCCESS"
                    )
                    logger.info("✅ Seeded dummy transaction logs")
        except Exception as e:
            logger.error(f"❌ Error during transactions schema verification/seeding: {e}")
            raise

        return cls._pool

    @classmethod
    async def close_pool(cls) -> None:
        """Close the asyncpg connection pool."""
        if cls._pool is not None:
            await cls._pool.close()
            cls._pool = None
            logger.info("✅ Database connection pool closed")

    # ---- asyncpg connection helpers (used by the asyncpg repositories) ---- #

    @classmethod
    async def get_connection(cls) -> asyncpg.Connection:
        """Get a connection from the pool."""
        if cls._pool is None:
            await cls.bootstrap_asyncpg()
        return await cls._pool.acquire()

    @classmethod
    async def execute(
        cls,
        query: str,
        *args,
        fetch: bool = False,
        fetch_one: bool = False
    ):
        """Execute a query."""
        conn = await cls.get_connection()
        try:
            if fetch:
                return await conn.fetch(query, *args)
            elif fetch_one:
                return await conn.fetchrow(query, *args)
            else:
                return await conn.execute(query, *args)
        finally:
            await cls._pool.release(conn)

    @classmethod
    async def transaction(cls):
        """Get a transaction context manager."""
        conn = await cls.get_connection()
        return conn.transaction()


# Singleton instance
database = DatabaseConnection()
