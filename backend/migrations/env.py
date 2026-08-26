"""
Alembic async migration environment.

Key design decisions:
  - Uses SQLAlchemy async engine (asyncpg driver) to match the application stack.
  - DATABASE_URL is read from environment variable with the same fallback
    used in app/core/database.py — single source of truth.
  - All four models (User, Department, Employee, AuditLog) are imported here
    so that autogenerate can detect schema changes automatically.
  - run_migrations_online() uses AsyncEngine.begin() for async compatibility.
"""
from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

import sys
from pathlib import Path

# Add backend root to sys.path so 'app' is importable
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# ---------------------------------------------------------------------------
# Import application Base and ALL models so autogenerate detects them
# ---------------------------------------------------------------------------
from app.models.base import Base          # DeclarativeBase
from app.models.user import User          # noqa: F401
from app.models.department import Department  # noqa: F401
from app.models.employee import Employee  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.attendance import Attendance  # noqa: F401
from app.models.leave import LeaveRequest, LeaveBalance  # noqa: F401
from app.models.payroll import PayrollPeriod, PayrollRecord  # noqa: F401
from app.models.notification import Notification  # noqa: F401


# ---------------------------------------------------------------------------
# Alembic Config object (gives access to values in alembic.ini)
# ---------------------------------------------------------------------------
config = context.config

# ---------------------------------------------------------------------------
# Inject DATABASE_URL — same default as app/core/database.py
# ---------------------------------------------------------------------------
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres",
)
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---------------------------------------------------------------------------
# Target metadata for autogenerate comparison
# ---------------------------------------------------------------------------
target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# Offline migrations (no live DB connection)
# ---------------------------------------------------------------------------
def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    Emits SQL to stdout without requiring a live DB connection.
    Useful for generating SQL scripts for DBA review.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Render column-level comments in DDL
        render_as_batch=False,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online migrations (async engine)
# ---------------------------------------------------------------------------
def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        # Include schema in autogenerate comparisons
        include_schemas=False,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Run migrations against a live async PostgreSQL connection.
    NullPool is used to prevent connection pool leaks during CLI execution.
    """
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
# Alembic dispatch
# ---------------------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
