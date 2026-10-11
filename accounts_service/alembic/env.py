"""Alembic environment (Enterprise remediation Phase 2 / unblocks H-4).

Binds Alembic to the service's SQLAlchemy models so migrations are versioned and
reversible instead of relying on Base.metadata.create_all at startup.

Migration URL resolution (sync driver — Alembic runs synchronously):
  1. ALEMBIC_DATABASE_URL env var, else
  2. sqlalchemy.url in alembic.ini (defaults to a local sqlite file).
Async drivers are coerced to their sync equivalents automatically, so the same
DATABASE_URL used at runtime can drive migrations.
"""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Make the service's `app` package importable when alembic runs from the service dir.
sys.path.insert(0, os.getcwd())
from app.database.orm_models import Base  # noqa: E402

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Resolve + normalise the URL to a SYNC driver for Alembic.
_url = os.getenv("ALEMBIC_DATABASE_URL") or config.get_main_option("sqlalchemy.url")
for _async, _sync in (("+aiosqlite", ""), ("+asyncpg", "+psycopg2"), ("+aiomysql", "+pymysql")):
    _url = _url.replace(_async, _sync)
config.set_main_option("sqlalchemy.url", _url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
