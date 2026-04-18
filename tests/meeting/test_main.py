"""Tests for meeting/main.py — written before implementation (TDD)."""

from unittest.mock import patch

import pytest

from pipeline.db import init_db, insert_idea
from meeting.main import _parse_conclusion, run_meeting


# --- _parse_conclusion unit tests ---

def test_parse_conclusion_detects_adoption_with_marker():
    assert _parse_conclusion("各意見を踏まえ\n結論: 採用") == "採用"


def test_parse_conclusion_rejects_partial_match():
    # "採用できません" contains 採用 as substring — must return 見送り
    assert _parse_conclusion("今回は採用できません。\n結論: 見送り\n見送り理由: 市場が小さい") == "見送り"


def test_parse_conclusion_detects_rejection():
    assert _parse_conclusion("結論: 見送り\n見送り理由: タイミングが悪い") == "見送り"


def test_parse_conclusion_empty_string_returns_rejection():
    assert _parse_conclusion("") == "見送り"


def test_parse_conclusion_adoption_without_marker_is_rejected():
    # 採用 appears as isolated word but without the full marker phrase
    assert _parse_conclusion("採用を検討した結果、見送りとする") == "見送り"


def test_parse_conclusion_realistic_ceo_output_adopted():
    text = (
        "全員の意見を総合的に評価しました。市場タイミングも良好です。\n"
        "結論: 採用\n"
        "次のアクション:\n1. MVP構築\n2. 初期ターゲット選定"
    )
    assert _parse_conclusion(text) == "採用"


def test_parse_conclusion_handles_markdown_bold_adoption():
    # Regression: id=11 で `結論: **採用**` が見送り扱いされたバグ
    assert _parse_conclusion("各意見を総合し、\n結論: **採用**\n次のアクション:") == "採用"


def test_parse_conclusion_handles_fullwidth_colon():
    assert _parse_conclusion("結論：採用\n次のアクション:") == "採用"


def test_parse_conclusion_handles_markdown_bold_rejection():
    # `**採用**` が本文に含まれても、結論マーカー直下は見送りなので見送り
    assert _parse_conclusion("**採用**の可能性を検討したが、\n結論: **見送り**") == "見送り"


def test_parse_conclusion_handles_bold_label_with_adoption():
    assert _parse_conclusion("**結論**: 採用\n次のアクション:") == "採用"


def _make_high_score_idea(conn) -> int:
    return insert_idea(
        conn,
        title="高スコアアイデア",
        description="説明文です。",
        eval_why_now=9,
        eval_differentiation=9,
        eval_feasibility=8,
        eval_market_size=8,
    )


def _make_low_score_idea(conn) -> int:
    return insert_idea(
        conn,
        title="低スコアアイデア",
        description="説明文です。",
        eval_why_now=5,
        eval_differentiation=5,
        eval_feasibility=5,
        eval_market_size=5,
    )


def test_run_meeting_creates_session_for_high_score_ideas(tmp_path):
    conn = init_db(tmp_path / "test.db")
    _make_high_score_idea(conn)

    with (
        patch("meeting.main.DB_PATH", tmp_path / "test.db"),
        patch("meeting.main.call_agent", return_value="結論: 見送り\n見送り理由: テスト"),
        patch("meeting.main.create_github_issue", return_value=""),
    ):
        run_meeting()

    rows = conn.execute("SELECT * FROM meeting_sessions").fetchall()
    assert len(rows) == 1


def test_run_meeting_skips_low_score_ideas(tmp_path):
    conn = init_db(tmp_path / "test.db")
    _make_low_score_idea(conn)

    with patch("meeting.main.DB_PATH", tmp_path / "test.db"):
        run_meeting()

    rows = conn.execute("SELECT * FROM meeting_sessions").fetchall()
    assert len(rows) == 0


def test_run_meeting_stores_messages_in_db(tmp_path):
    conn = init_db(tmp_path / "test.db")
    _make_high_score_idea(conn)

    with (
        patch("meeting.main.DB_PATH", tmp_path / "test.db"),
        patch("meeting.main.call_agent", return_value="テスト発言"),
        patch("meeting.main.create_github_issue", return_value=""),
    ):
        run_meeting()

    rows = conn.execute("SELECT * FROM meeting_messages").fetchall()
    assert len(rows) > 0


def test_run_meeting_creates_issue_when_adopted(tmp_path):
    conn = init_db(tmp_path / "test.db")
    _make_high_score_idea(conn)

    turn_counter = {"n": 0}

    def fake_call_agent(role, idea, history):
        turn_counter["n"] += 1
        if role == "ceo" and turn_counter["n"] > 2:
            return "結論: 採用\n次のアクション:\n1. MVP を構築する"
        return "テスト発言"

    with (
        patch("meeting.main.DB_PATH", tmp_path / "test.db"),
        patch("meeting.main.call_agent", side_effect=fake_call_agent),
        patch.dict("os.environ", {"GITHUB_REPOSITORY": "owner/repo", "GITHUB_TOKEN": "ghp_test"}),
        patch(
            "meeting.main.create_github_issue",
            return_value="https://github.com/owner/repo/issues/1",
        ) as mock_issue,
    ):
        run_meeting()

    mock_issue.assert_called_once()
    row = conn.execute("SELECT * FROM meeting_sessions").fetchone()
    assert row["conclusion"] == "採用"
    assert row["github_issue_url"] == "https://github.com/owner/repo/issues/1"


def test_run_meeting_does_not_create_issue_when_rejected(tmp_path):
    conn = init_db(tmp_path / "test.db")
    _make_high_score_idea(conn)

    with (
        patch("meeting.main.DB_PATH", tmp_path / "test.db"),
        patch("meeting.main.call_agent", return_value="結論: 見送り\n見送り理由: 市場が小さい"),
        patch("meeting.main.create_github_issue", return_value="") as mock_issue,
    ):
        run_meeting()

    mock_issue.assert_not_called()
    row = conn.execute("SELECT * FROM meeting_sessions").fetchone()
    assert row["conclusion"] == "見送り"


def test_run_meeting_skips_already_discussed_ideas(tmp_path):
    conn = init_db(tmp_path / "test.db")
    idea_id = _make_high_score_idea(conn)
    conn.execute(
        "INSERT INTO meeting_sessions (idea_id, conclusion) VALUES (?, ?)",
        (idea_id, "採用"),
    )
    conn.commit()

    with (
        patch("meeting.main.DB_PATH", tmp_path / "test.db"),
        patch("meeting.main.call_agent", return_value="テスト発言") as mock_agent,
    ):
        run_meeting()

    mock_agent.assert_not_called()
