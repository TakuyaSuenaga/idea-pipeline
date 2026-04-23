"""Tests for meeting/db.py — written before implementation (TDD)."""

import pytest
from pipeline.db import init_db, insert_idea
from meeting.db import (
    get_ideas_for_meeting,
    create_meeting_session,
    add_meeting_message,
    update_meeting_conclusion,
    update_personal_scores,
)


def _make_idea(conn, eval_why_now: int = 8) -> int:
    return insert_idea(
        conn,
        title="テストアイデア",
        description="テスト用の説明文です。",
        eval_why_now=eval_why_now,
        eval_differentiation=eval_why_now,
        eval_feasibility=eval_why_now,
        eval_market_size=eval_why_now,
    )


# ---------------------------------------------------------------------------
# get_ideas_for_meeting
# ---------------------------------------------------------------------------

def test_get_ideas_for_meeting_returns_high_score_ideas(tmp_path):
    conn = init_db(tmp_path / "test.db")
    idea_id = _make_idea(conn, eval_why_now=8)
    ideas = get_ideas_for_meeting(conn, min_score=7.0)
    assert len(ideas) == 1
    assert ideas[0]["id"] == idea_id


def test_get_ideas_for_meeting_excludes_low_score(tmp_path):
    conn = init_db(tmp_path / "test.db")
    _make_idea(conn, eval_why_now=5)
    ideas = get_ideas_for_meeting(conn, min_score=7.0)
    assert ideas == []


def test_get_ideas_for_meeting_excludes_already_discussed(tmp_path):
    conn = init_db(tmp_path / "test.db")
    idea_id = _make_idea(conn)
    session_id = create_meeting_session(conn, idea_id)
    update_meeting_conclusion(conn, session_id, "採用")
    ideas = get_ideas_for_meeting(conn, min_score=7.0)
    assert ideas == []


def test_get_ideas_for_meeting_respects_limit(tmp_path):
    conn = init_db(tmp_path / "test.db")
    for _ in range(5):
        _make_idea(conn)
    ideas = get_ideas_for_meeting(conn, min_score=7.0, limit=3)
    assert len(ideas) == 3


def test_get_ideas_for_meeting_ordered_by_score_desc(tmp_path):
    conn = init_db(tmp_path / "test.db")
    _make_idea(conn, eval_why_now=7)
    _make_idea(conn, eval_why_now=10)
    ideas = get_ideas_for_meeting(conn, min_score=7.0)
    assert ideas[0]["eval_total"] >= ideas[1]["eval_total"]


# ---------------------------------------------------------------------------
# create_meeting_session
# ---------------------------------------------------------------------------

def test_create_meeting_session_returns_id(tmp_path):
    conn = init_db(tmp_path / "test.db")
    idea_id = _make_idea(conn)
    session_id = create_meeting_session(conn, idea_id)
    assert isinstance(session_id, int)
    assert session_id > 0


def test_create_meeting_session_stores_idea_id(tmp_path):
    conn = init_db(tmp_path / "test.db")
    idea_id = _make_idea(conn)
    session_id = create_meeting_session(conn, idea_id)
    row = conn.execute("SELECT * FROM meeting_sessions WHERE id = ?", (session_id,)).fetchone()
    assert row["idea_id"] == idea_id
    assert row["conclusion"] is None
    assert row["github_issue_url"] is None


# ---------------------------------------------------------------------------
# add_meeting_message
# ---------------------------------------------------------------------------

def test_add_meeting_message_returns_id(tmp_path):
    conn = init_db(tmp_path / "test.db")
    idea_id = _make_idea(conn)
    session_id = create_meeting_session(conn, idea_id)
    msg_id = add_meeting_message(conn, session_id, "ceo", 0, "議題を開始します。")
    assert isinstance(msg_id, int)
    assert msg_id > 0


def test_add_meeting_message_stores_content(tmp_path):
    conn = init_db(tmp_path / "test.db")
    idea_id = _make_idea(conn)
    session_id = create_meeting_session(conn, idea_id)
    add_meeting_message(conn, session_id, "planning", 1, "企画観点: 賛成")
    row = conn.execute(
        "SELECT * FROM meeting_messages WHERE session_id = ?", (session_id,)
    ).fetchone()
    assert row["agent_role"] == "planning"
    assert row["turn"] == 1
    assert row["content"] == "企画観点: 賛成"


def test_add_multiple_messages_same_session(tmp_path):
    conn = init_db(tmp_path / "test.db")
    idea_id = _make_idea(conn)
    session_id = create_meeting_session(conn, idea_id)
    for i, role in enumerate(["ceo", "planning", "sales"]):
        add_meeting_message(conn, session_id, role, i, f"{role}の発言")
    rows = conn.execute(
        "SELECT * FROM meeting_messages WHERE session_id = ? ORDER BY turn", (session_id,)
    ).fetchall()
    assert len(rows) == 3
    assert rows[0]["agent_role"] == "ceo"


# ---------------------------------------------------------------------------
# update_meeting_conclusion
# ---------------------------------------------------------------------------

def test_update_meeting_conclusion_adopted(tmp_path):
    conn = init_db(tmp_path / "test.db")
    idea_id = _make_idea(conn)
    session_id = create_meeting_session(conn, idea_id)
    update_meeting_conclusion(conn, session_id, "採用", "https://github.com/owner/repo/issues/1")
    row = conn.execute("SELECT * FROM meeting_sessions WHERE id = ?", (session_id,)).fetchone()
    assert row["conclusion"] == "採用"
    assert row["github_issue_url"] == "https://github.com/owner/repo/issues/1"


def test_update_meeting_conclusion_rejected(tmp_path):
    conn = init_db(tmp_path / "test.db")
    idea_id = _make_idea(conn)
    session_id = create_meeting_session(conn, idea_id)
    update_meeting_conclusion(conn, session_id, "見送り")
    row = conn.execute("SELECT * FROM meeting_sessions WHERE id = ?", (session_id,)).fetchone()
    assert row["conclusion"] == "見送り"
    assert row["github_issue_url"] is None


# ---------------------------------------------------------------------------
# update_personal_scores
# ---------------------------------------------------------------------------

def test_update_personal_scores_stores_values(tmp_path):
    conn = init_db(tmp_path / "test.db")
    idea_id = _make_idea(conn)
    session_id = create_meeting_session(conn, idea_id)
    update_personal_scores(conn, session_id, japan_demand=2, solo_customer=3, revenue_6mo=1, background_fit=3)
    row = conn.execute("SELECT * FROM meeting_sessions WHERE id = ?", (session_id,)).fetchone()
    assert row["personal_japan_demand"] == 2
    assert row["personal_solo_customer"] == 3
    assert row["personal_revenue_6mo"] == 1
    assert row["personal_background_fit"] == 3


def test_update_personal_scores_accepts_none_values(tmp_path):
    conn = init_db(tmp_path / "test.db")
    idea_id = _make_idea(conn)
    session_id = create_meeting_session(conn, idea_id)
    update_personal_scores(conn, session_id, japan_demand=None, solo_customer=None, revenue_6mo=None, background_fit=None)
    row = conn.execute("SELECT * FROM meeting_sessions WHERE id = ?", (session_id,)).fetchone()
    assert row["personal_japan_demand"] is None
    assert row["personal_solo_customer"] is None
