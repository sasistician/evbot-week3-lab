"""Conversational session memory — SQLite-backed.

Deliberately a separate concern from the vector-DB knowledge base (see
rag/retriever.py): this stores what was *said* in a conversation, not what's
*known* about EVs. Persists across process restarts.
"""

import sqlite3
from dataclasses import dataclass

from evbot.config import MEMORY_DB_PATH

_SCHEMA = """
CREATE TABLE IF NOT EXISTS turns (
    session_id TEXT NOT NULL,
    turn_index INTEGER NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    ts TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


@dataclass
class Turn:
    role: str
    content: str


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute(_SCHEMA)
    return conn


def append_turn(session_id: str, role: str, content: str, db_path: str = MEMORY_DB_PATH) -> None:
    with _connect(db_path) as conn:
        next_index = conn.execute(
            "SELECT COALESCE(MAX(turn_index), -1) + 1 FROM turns WHERE session_id = ?",
            (session_id,),
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO turns (session_id, turn_index, role, content) VALUES (?, ?, ?, ?)",
            (session_id, next_index, role, content),
        )


def get_recent_turns(session_id: str, n: int = 6, db_path: str = MEMORY_DB_PATH) -> list[Turn]:
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT role, content FROM turns WHERE session_id = ? "
            "ORDER BY turn_index DESC LIMIT ?",
            (session_id, n),
        ).fetchall()
    return [Turn(role=role, content=content) for role, content in reversed(rows)]
