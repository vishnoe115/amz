"""Durable storage for Orpheus' Amazon login session blob."""

import os
from pathlib import Path

import psycopg2


SESSION_KEY = "amazonmusic_loginstorage_v1"
SESSION_PATH = Path("/app/config/loginstorage.bin")


def _database_url() -> str:
    return os.environ.get("DATABASE_URL", "").strip()


def _ensure_table(connection) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS amz_runtime_state (
                state_key TEXT PRIMARY KEY,
                state_value BYTEA NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
    connection.commit()


def restore_session_from_database() -> bool:
    """Restore loginstorage.bin only when a database backup exists."""
    database_url = _database_url()
    if not database_url:
        return False
    with psycopg2.connect(database_url) as connection:
        _ensure_table(connection)
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT state_value FROM amz_runtime_state WHERE state_key = %s",
                (SESSION_KEY,),
            )
            row = cursor.fetchone()
    if not row:
        return False
    SESSION_PATH.parent.mkdir(parents=True, exist_ok=True)
    SESSION_PATH.write_bytes(bytes(row[0]))
    SESSION_PATH.chmod(0o600)
    return True


def save_session_to_database() -> bool:
    """Upsert the current Amazon session file as PostgreSQL BYTEA."""
    database_url = _database_url()
    if not database_url or not SESSION_PATH.is_file():
        return False
    payload = SESSION_PATH.read_bytes()
    if not payload:
        return False
    with psycopg2.connect(database_url) as connection:
        _ensure_table(connection)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO amz_runtime_state (state_key, state_value, updated_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (state_key) DO UPDATE SET
                    state_value = EXCLUDED.state_value,
                    updated_at = NOW()
                """,
                (SESSION_KEY, psycopg2.Binary(payload)),
            )
        connection.commit()
    return True
