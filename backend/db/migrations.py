"""Lightweight SQLite schema upgrades for existing audit databases.

``create_all`` only creates new tables; it does not add columns to tables that
already exist. This module applies idempotent ``ALTER TABLE`` statements on
startup so local ``audit.db`` files stay compatible after model changes.
"""

from __future__ import annotations

import logging

from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection

from backend.db.session import Base

logger = logging.getLogger(__name__)

# table_name -> list of (column_name, column_ddl_suffix)
_COLUMN_PATCHES: dict[str, list[tuple[str, str]]] = {
    "conversations": [
        ("retrieval_mrr", "FLOAT"),
        ("retrieval_ndcg", "FLOAT"),
        ("retrieval_keyword_coverage", "FLOAT"),
        ("clarification_rounds", "INTEGER NOT NULL DEFAULT 0"),
    ],
}


def _existing_columns(connection: Connection, table: str) -> set[str]:
    inspector = inspect(connection)
    if table not in inspector.get_table_names():
        return set()
    return {col["name"] for col in inspector.get_columns(table)}


def apply_sqlite_migrations(connection: Connection) -> None:
    """Add any model columns missing from the on-disk SQLite schema."""
    for table, patches in _COLUMN_PATCHES.items():
        existing = _existing_columns(connection, table)
        if not existing:
            continue
        for column_name, ddl in patches:
            if column_name in existing:
                continue
            sql = f"ALTER TABLE {table} ADD COLUMN {column_name} {ddl}"
            logger.info("Applying migration: %s", sql)
            connection.execute(text(sql))


async def run_migrations(async_connection) -> None:
    await async_connection.run_sync(apply_sqlite_migrations)
