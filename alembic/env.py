from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import create_engine, pool

from alembic import context

# Project root (parent of alembic/)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.models import Base  # noqa: E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _sync_database_url() -> str:
    """Alembic uses a synchronous engine; map async URLs to sync drivers."""
    raw = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./db.sqlite3")
    if raw.startswith("sqlite+aiosqlite"):
        remainder = raw.removeprefix("sqlite+aiosqlite:")
        return f"sqlite:{remainder}"
    if raw.startswith("postgresql+asyncpg://"):
        return "postgresql+psycopg2://" + raw.removeprefix("postgresql+asyncpg://")
    return raw


def run_migrations_offline() -> None:
    url = _sync_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(_sync_database_url(), poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
