"""SQLite database operations for idea-pipeline."""

import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "ideas.db"

_CREATE_MARKET_RESEARCH = """
CREATE TABLE IF NOT EXISTS market_research (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    source    TEXT NOT NULL,
    title     TEXT NOT NULL,
    url       TEXT,
    content   TEXT,
    score     INTEGER,
    category  TEXT,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

_CREATE_STARTUP_IDEAS = """
CREATE TABLE IF NOT EXISTS startup_ideas (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    title         TEXT NOT NULL,
    description   TEXT NOT NULL,
    target_market TEXT,
    why_now       TEXT,
    revenue_model TEXT,
    difficulty    TEXT,
    category      TEXT,
    research_ids  TEXT,
    generated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def init_db(db_path: str | Path = DB_PATH) -> sqlite3.Connection:
    """Create (or open) the SQLite DB and ensure both tables exist."""
    conn = sqlite3.connect(str(db_path), timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(_CREATE_MARKET_RESEARCH)
    conn.execute(_CREATE_STARTUP_IDEAS)
    conn.commit()
    return conn


def insert_research(
    conn: sqlite3.Connection,
    source: str,
    title: str,
    url: str | None = None,
    content: str | None = None,
    score: int | None = None,
    category: str | None = None,
) -> int:
    """Insert a market research item and return its row id."""
    cursor = conn.execute(
        """
        INSERT INTO market_research (source, title, url, content, score, category)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (source, title, url, content, score, category),
    )
    conn.commit()
    return cursor.lastrowid


def fetch_recent_research(conn: sqlite3.Connection, days: int = 7) -> list[dict]:
    """Return research items fetched within the last *days* days."""
    cursor = conn.execute(
        """
        SELECT * FROM market_research
        WHERE fetched_at >= datetime('now', ?)
        ORDER BY fetched_at DESC
        """,
        (f"-{days} days",),
    )
    return [dict(row) for row in cursor.fetchall()]


def cleanup_old_research(conn: sqlite3.Connection, days: int = 7) -> int:
    """Delete research older than *days* days. Returns number of rows deleted."""
    cursor = conn.execute(
        "DELETE FROM market_research WHERE fetched_at < datetime('now', ?)",
        (f"-{days} days",),
    )
    conn.commit()
    return cursor.rowcount


def insert_idea(
    conn: sqlite3.Connection,
    title: str,
    description: str,
    target_market: str | None = None,
    why_now: str | None = None,
    revenue_model: str | None = None,
    difficulty: str | None = None,
    category: str | None = None,
    research_ids: list[int] | None = None,
) -> int:
    """Insert a startup idea and return its row id."""
    cursor = conn.execute(
        """
        INSERT INTO startup_ideas
            (title, description, target_market, why_now, revenue_model,
             difficulty, category, research_ids)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            title,
            description,
            target_market,
            why_now,
            revenue_model,
            difficulty,
            category,
            json.dumps(research_ids or []),
        ),
    )
    conn.commit()
    return cursor.lastrowid


def fetch_all_ideas(conn: sqlite3.Connection, limit: int = 100) -> list[dict]:
    """Return all startup ideas, newest first."""
    cursor = conn.execute(
        "SELECT * FROM startup_ideas ORDER BY generated_at DESC, id DESC LIMIT ?",
        (limit,),
    )
    rows = [dict(row) for row in cursor.fetchall()]
    for row in rows:
        try:
            row["research_ids"] = json.loads(row["research_ids"] or "[]")
        except (json.JSONDecodeError, TypeError):
            row["research_ids"] = []
    return rows
