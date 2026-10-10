"""
backend/database.py
===================
Database engine, session factory, and declarative Base for the
Crop Disease Detection API.

Responsibilities:
  - Build the async SQLAlchemy engine from config.py (which reads .env)
  - Expose an async session factory  (AsyncSessionLocal)
  - Provide the shared declarative Base used by all ORM models
  - Expose get_db() — a FastAPI dependency that yields a DB session
    and commits / rolls back automatically

This file does NOT define any models or seed any data.
Import DATABASE_URL from config, not from here.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

# config.py owns .env loading and URL construction
from config import DATABASE_URL, DEBUG_SQL

# ---------------------------------------------------------------------------
# Async engine
# pool_pre_ping=True  — validate connections before use (handles DB restarts)
# echo=DEBUG_SQL      — log all SQL when DEBUG_SQL=true in .env
# ---------------------------------------------------------------------------
engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=DEBUG_SQL,
)

# ---------------------------------------------------------------------------
# Async session factory
# expire_on_commit=False — keep ORM attributes accessible after commit
# ---------------------------------------------------------------------------
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ---------------------------------------------------------------------------
# Declarative Base — imported by all model files
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    """Shared SQLAlchemy declarative base for all ORM models."""
    pass


# ---------------------------------------------------------------------------
# FastAPI dependency — yields a managed DB session per request
# ---------------------------------------------------------------------------
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides a managed async database session.

    Usage in a route:
        @app.get("/example")
        async def example(db: AsyncSession = Depends(get_db)):
            ...

    Lifecycle per request:
      - yields a fresh session
      - commits on clean return
      - rolls back on any exception
      - always closes at the end
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ---------------------------------------------------------------------------
# Database connectivity test helper
# ---------------------------------------------------------------------------
async def check_db_connection() -> dict:
    """
    Test direct PostgreSQL database connectivity and return status metrics.
    Safe for health checks, connection diagnostics, and startup checks.
    """
    import time
    from sqlalchemy import text
    from config import DB_HOST, DB_NAME, DB_PORT

    start_time = time.monotonic()
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version();"))
            version_str = result.scalar()
            latency_ms = round((time.monotonic() - start_time) * 1000, 2)
            return {
                "connected": True,
                "latency_ms": latency_ms,
                "version": version_str,
                "database": DB_NAME,
                "host": DB_HOST,
                "port": DB_PORT,
            }
    except Exception as exc:
        latency_ms = round((time.monotonic() - start_time) * 1000, 2)
        return {
            "connected": False,
            "latency_ms": latency_ms,
            "error": str(exc),
            "database": DB_NAME,
            "host": DB_HOST,
            "port": DB_PORT,
        }

