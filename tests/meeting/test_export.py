"""Tests for meeting/export.py — written before implementation (TDD)."""

import json
from pipeline.db import init_db, insert_idea
from meeting.db import create_meeting_session, add_meeting_message, update_meeting_conclusion
from meeting.export import export_meetings


def _setup_session(conn, conclusion: str = "採用", issue_url: str = "") -> tuple[int, int]:
    idea_id = insert_idea(
        conn, title="テストアイデア", description="説明", eval_why_now=9,
        eval_differentiation=9, eval_feasibility=8, eval_market_size=8,
    )
    session_id = create_meeting_session(conn, idea_id)
    add_meeting_message(conn, session_id, "ceo", 0, "議題を開始します。")
    add_meeting_message(conn, session_id, "planning", 1, "企画観点: 賛成")
    update_meeting_conclusion(conn, session_id, conclusion, issue_url or None)
    return idea_id, session_id


def test_export_meetings_creates_json_file(tmp_path, monkeypatch):
    monkeypatch.setattr("meeting.export.MEETINGS_JSON_PATH", tmp_path / "meetings.json")
    conn = init_db(tmp_path / "test.db")
    _setup_session(conn)
    export_meetings(conn)
    assert (tmp_path / "meetings.json").exists()


def test_export_meetings_json_structure(tmp_path, monkeypatch):
    monkeypatch.setattr("meeting.export.MEETINGS_JSON_PATH", tmp_path / "meetings.json")
    conn = init_db(tmp_path / "test.db")
    _setup_session(conn)
    export_meetings(conn)
    data = json.loads((tmp_path / "meetings.json").read_text(encoding="utf-8"))
    assert "exported_at" in data
    assert "count" in data
    assert "sessions" in data
    assert data["count"] == 1


def test_export_meetings_session_has_expected_fields(tmp_path, monkeypatch):
    monkeypatch.setattr("meeting.export.MEETINGS_JSON_PATH", tmp_path / "meetings.json")
    conn = init_db(tmp_path / "test.db")
    _setup_session(conn, conclusion="採用", issue_url="https://github.com/owner/repo/issues/1")
    export_meetings(conn)
    data = json.loads((tmp_path / "meetings.json").read_text(encoding="utf-8"))
    session = data["sessions"][0]
    assert session["idea_title"] == "テストアイデア"
    assert session["conclusion"] == "採用"
    assert session["github_issue_url"] == "https://github.com/owner/repo/issues/1"
    assert "held_at" in session
    assert "messages" in session


def test_export_meetings_messages_ordered_by_turn(tmp_path, monkeypatch):
    monkeypatch.setattr("meeting.export.MEETINGS_JSON_PATH", tmp_path / "meetings.json")
    conn = init_db(tmp_path / "test.db")
    _setup_session(conn)
    export_meetings(conn)
    data = json.loads((tmp_path / "meetings.json").read_text(encoding="utf-8"))
    messages = data["sessions"][0]["messages"]
    assert len(messages) == 2
    assert messages[0]["agent_role"] == "ceo"
    assert messages[0]["turn"] == 0
    assert messages[1]["agent_role"] == "planning"
    assert messages[1]["turn"] == 1


def test_export_meetings_message_has_content(tmp_path, monkeypatch):
    monkeypatch.setattr("meeting.export.MEETINGS_JSON_PATH", tmp_path / "meetings.json")
    conn = init_db(tmp_path / "test.db")
    _setup_session(conn)
    export_meetings(conn)
    data = json.loads((tmp_path / "meetings.json").read_text(encoding="utf-8"))
    msg = data["sessions"][0]["messages"][0]
    assert msg["content"] == "議題を開始します。"
    assert "agent_role" in msg
    assert "turn" in msg


def test_export_meetings_sessions_newest_first(tmp_path, monkeypatch):
    monkeypatch.setattr("meeting.export.MEETINGS_JSON_PATH", tmp_path / "meetings.json")
    conn = init_db(tmp_path / "test.db")
    for title in ["最初のアイデア", "次のアイデア"]:
        idea_id = insert_idea(conn, title=title, description="desc",
                              eval_why_now=8, eval_differentiation=8,
                              eval_feasibility=8, eval_market_size=8)
        session_id = create_meeting_session(conn, idea_id)
        update_meeting_conclusion(conn, session_id, "見送り")
    export_meetings(conn)
    data = json.loads((tmp_path / "meetings.json").read_text(encoding="utf-8"))
    assert data["count"] == 2
    assert data["sessions"][0]["id"] > data["sessions"][1]["id"]


def test_export_meetings_empty_when_no_sessions(tmp_path, monkeypatch):
    monkeypatch.setattr("meeting.export.MEETINGS_JSON_PATH", tmp_path / "meetings.json")
    conn = init_db(tmp_path / "test.db")
    export_meetings(conn)
    data = json.loads((tmp_path / "meetings.json").read_text(encoding="utf-8"))
    assert data["count"] == 0
    assert data["sessions"] == []
