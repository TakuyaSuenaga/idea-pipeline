"""Tests for pipeline/db.py — written first (TDD)."""

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from pipeline.db import (
    cleanup_old_research,
    fetch_all_ideas,
    fetch_recent_research,
    init_db,
    insert_idea,
    insert_research,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_conn(tmp_path: Path) -> sqlite3.Connection:
    return init_db(tmp_path / "test.db")


def _research_kwargs(**overrides):
    base = dict(
        source="hackernews",
        title="Test Story",
        url="https://example.com/1",
        content="Some content",
        score=100,
        category="saas",
    )
    base.update(overrides)
    return base


def _idea_kwargs(**overrides):
    base = dict(
        title="Test Idea",
        description="An idea description.",
        target_market="Solo devs",
        why_now="AI makes it possible now",
        revenue_model="Subscription",
        difficulty="low",
        category="saas",
        research_ids=[1, 2],
        eval_why_now=8,
        eval_differentiation=7,
        eval_feasibility=9,
        eval_market_size=6,
        eval_comment="市場規模は中程度だが、実現可能性が高い。",
    )
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# init_db
# ---------------------------------------------------------------------------

def test_init_db_creates_both_tables(tmp_path):
    conn = _make_conn(tmp_path)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    assert "market_research" in tables
    assert "startup_ideas" in tables
    conn.close()


def test_init_db_is_idempotent(tmp_path):
    """Calling init_db twice on same file must not raise."""
    db_path = tmp_path / "test.db"
    conn1 = init_db(db_path)
    conn1.close()
    conn2 = init_db(db_path)
    conn2.close()


def test_init_db_migrates_eval_columns(tmp_path):
    """init_db on a DB lacking eval columns must add them without error."""
    db_path = tmp_path / "old.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE startup_ideas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

    conn = init_db(db_path)
    cols = {row[1] for row in conn.execute("PRAGMA table_info(startup_ideas)")}
    for expected in ("eval_why_now", "eval_differentiation", "eval_feasibility", "eval_market_size", "eval_comment", "eval_total"):
        assert expected in cols, f"Missing column: {expected}"
    conn.close()


# ---------------------------------------------------------------------------
# insert_research / fetch_recent_research
# ---------------------------------------------------------------------------

def test_insert_research_returns_row_id(tmp_path):
    conn = _make_conn(tmp_path)
    row_id = insert_research(conn, **_research_kwargs())
    assert isinstance(row_id, int)
    assert row_id > 0
    conn.close()


def test_fetch_recent_research_returns_inserted_row(tmp_path):
    conn = _make_conn(tmp_path)
    insert_research(conn, **_research_kwargs(title="Alpha"))
    rows = fetch_recent_research(conn, days=7)
    assert len(rows) == 1
    assert rows[0]["title"] == "Alpha"
    assert rows[0]["source"] == "hackernews"
    conn.close()


def test_fetch_recent_research_excludes_old_rows(tmp_path):
    conn = _make_conn(tmp_path)
    row_id = insert_research(conn, **_research_kwargs(title="Old"))
    old_ts = (datetime.now(timezone.utc) - timedelta(days=10)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    conn.execute(
        "UPDATE market_research SET fetched_at = ? WHERE id = ?", (old_ts, row_id)
    )
    conn.commit()
    rows = fetch_recent_research(conn, days=7)
    assert rows == []
    conn.close()


def test_fetch_recent_research_returns_dict_with_expected_keys(tmp_path):
    conn = _make_conn(tmp_path)
    insert_research(conn, **_research_kwargs())
    rows = fetch_recent_research(conn, days=7)
    expected_keys = {"id", "source", "title", "url", "content", "score", "category", "fetched_at"}
    assert expected_keys.issubset(rows[0].keys())
    conn.close()


# ---------------------------------------------------------------------------
# cleanup_old_research
# ---------------------------------------------------------------------------

def test_cleanup_removes_rows_older_than_days(tmp_path):
    conn = _make_conn(tmp_path)
    row_id = insert_research(conn, **_research_kwargs())
    old_ts = (datetime.now(timezone.utc) - timedelta(days=10)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    conn.execute(
        "UPDATE market_research SET fetched_at = ? WHERE id = ?", (old_ts, row_id)
    )
    conn.commit()
    deleted = cleanup_old_research(conn, days=7)
    assert deleted == 1
    assert fetch_recent_research(conn, days=7) == []
    conn.close()


def test_cleanup_keeps_recent_rows(tmp_path):
    conn = _make_conn(tmp_path)
    insert_research(conn, **_research_kwargs())
    deleted = cleanup_old_research(conn, days=7)
    assert deleted == 0
    assert len(fetch_recent_research(conn, days=7)) == 1
    conn.close()


def test_cleanup_returns_count_of_deleted_rows(tmp_path):
    conn = _make_conn(tmp_path)
    old_ts = (datetime.now(timezone.utc) - timedelta(days=10)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    for i in range(3):
        row_id = insert_research(
            conn, **_research_kwargs(title=f"Old {i}", url=f"https://example.com/{i}")
        )
        conn.execute(
            "UPDATE market_research SET fetched_at = ? WHERE id = ?", (old_ts, row_id)
        )
    conn.commit()
    assert cleanup_old_research(conn, days=7) == 3
    conn.close()


# ---------------------------------------------------------------------------
# insert_idea / fetch_all_ideas
# ---------------------------------------------------------------------------

def test_insert_idea_returns_row_id(tmp_path):
    conn = _make_conn(tmp_path)
    row_id = insert_idea(conn, **_idea_kwargs())
    assert isinstance(row_id, int)
    assert row_id > 0
    conn.close()


def test_fetch_all_ideas_returns_inserted_idea(tmp_path):
    conn = _make_conn(tmp_path)
    insert_idea(conn, **_idea_kwargs(title="My Idea"))
    ideas = fetch_all_ideas(conn)
    assert len(ideas) == 1
    assert ideas[0]["title"] == "My Idea"
    conn.close()


def test_fetch_all_ideas_newest_first(tmp_path):
    conn = _make_conn(tmp_path)
    id1 = insert_idea(conn, **_idea_kwargs(title="First"))
    id2 = insert_idea(conn, **_idea_kwargs(title="Second"))
    ideas = fetch_all_ideas(conn)
    assert ideas[0]["id"] == id2
    assert ideas[1]["id"] == id1
    conn.close()


def test_fetch_all_ideas_deserializes_research_ids(tmp_path):
    conn = _make_conn(tmp_path)
    insert_idea(conn, **_idea_kwargs(research_ids=[10, 20, 30]))
    ideas = fetch_all_ideas(conn)
    assert ideas[0]["research_ids"] == [10, 20, 30]
    conn.close()


def test_ideas_not_deleted_by_cleanup(tmp_path):
    """cleanup_old_research must never touch the startup_ideas table."""
    conn = _make_conn(tmp_path)
    insert_idea(conn, **_idea_kwargs())
    cleanup_old_research(conn, days=0)
    assert len(fetch_all_ideas(conn)) == 1
    conn.close()


def test_fetch_all_ideas_respects_limit(tmp_path):
    conn = _make_conn(tmp_path)
    for i in range(5):
        insert_idea(conn, **_idea_kwargs(title=f"Idea {i}"))
    ideas = fetch_all_ideas(conn, limit=3)
    assert len(ideas) == 3
    conn.close()


def test_insert_idea_saves_eval_fields(tmp_path):
    conn = _make_conn(tmp_path)
    insert_idea(conn, **_idea_kwargs())
    ideas = fetch_all_ideas(conn)
    idea = ideas[0]
    assert idea["eval_why_now"] == 8
    assert idea["eval_differentiation"] == 7
    assert idea["eval_feasibility"] == 9
    assert idea["eval_market_size"] == 6
    assert idea["eval_comment"] == "市場規模は中程度だが、実現可能性が高い。"
    conn.close()


def test_insert_idea_computes_eval_total(tmp_path):
    """eval_total should be the average of the 4 score fields (rounded to 1 decimal)."""
    conn = _make_conn(tmp_path)
    insert_idea(conn, **_idea_kwargs())  # scores: 8, 7, 9, 6 → avg 7.5
    ideas = fetch_all_ideas(conn)
    assert ideas[0]["eval_total"] == 7.5
    conn.close()


def test_insert_idea_eval_total_none_when_no_scores(tmp_path):
    """eval_total should be None when all eval scores are None."""
    conn = _make_conn(tmp_path)
    insert_idea(conn, **_idea_kwargs(
        eval_why_now=None, eval_differentiation=None,
        eval_feasibility=None, eval_market_size=None,
        eval_comment=None,
    ))
    ideas = fetch_all_ideas(conn)
    assert ideas[0]["eval_total"] is None
    conn.close()
