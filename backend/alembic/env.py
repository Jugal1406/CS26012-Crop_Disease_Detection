"""
backend/alembic/env.py
======================
Alembic environment configuration for the Crop Disease Detection backend.

Configured for:
  - Async PostgreSQL driver (asyncpg via SQLAlchemy)
  - Autogenerate support (imports all models so Alembic can diff them)
  - Database URL read from environment variables via python-dotenv

How to use:
  # Create a new migration (autogenerate from model diff):
  alembic revision --autogenerate -m "description"

  # Apply all pending migrations:
  alembic upgrade head

  # Downgrade one step:
  alembic downgrade -1
"""

import asyncio
import os
from logging.config import fileConfig

from dotenv import load_dotenv
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# ---------------------------------------------------------------------------
# Load .env so DATABASE_URL is available when running CLI commands
# ---------------------------------------------------------------------------
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

# ---------------------------------------------------------------------------
# Alembic Config object — provides access to values in alembic.ini
# ---------------------------------------------------------------------------
config = context.config

# ---------------------------------------------------------------------------
# Set the database URL from environment variables (overrides alembic.ini)
# ---------------------------------------------------------------------------
_DB_HOST = os.getenv("DB_HOST", "localhost")
_DB_PORT = os.getenv("DB_PORT", "5432")
_DB_NAME = os.getenv("DB_NAME", "crop_disease_db")
_DB_USER = os.getenv("DB_USER", "postgres")
_DB_PASSWORD = os.getenv("DB_PASSWORD", "")

_DATABASE_URL = (
    f"postgresql+asyncpg://{_DB_USER}:{_DB_PASSWORD}"
    f"@{_DB_HOST}:{_DB_PORT}/{_DB_NAME}"
)
config.set_main_option("sqlalchemy.url", _DATABASE_URL)

# ---------------------------------------------------------------------------
# Python logging from alembic.ini
# ---------------------------------------------------------------------------
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---------------------------------------------------------------------------
# Import ALL models so Alembic can autogenerate complete diffs.
# Adding a new model = add its import here.
# ---------------------------------------------------------------------------
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database import Base  # noqa: F401 — loads the declarative base
import models  # noqa: F401 — registers all 9 tables on Base.metadata

target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# Offline migration (generates SQL script without a live DB connection)
# ---------------------------------------------------------------------------
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online migration (runs against a live async DB connection)
# ---------------------------------------------------------------------------
def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations through a sync connection."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for online (live DB) migrations."""
    asyncio.run(run_async_migrations())


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
