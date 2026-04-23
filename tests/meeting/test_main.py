"""Tests for meeting/main.py — written before implementation (TDD)."""

from unittest.mock import patch

import pytest

from pipeline.db import init_db, insert_idea
from meeting.main import _parse_conclusion, _parse_personal_scores, run_meeting


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


# ---------------------------------------------------------------------------
# _parse_personal_scores
# ---------------------------------------------------------------------------

def test_parse_personal_scores_extracts_all_scores():
    text = (
        "個人文脈スコア:\n"
        "- 日本市場需要: 2/3\n"
        "- 初顧客獲得可能性: 3/3\n"
        "- 6ヶ月収益化: 1/3\n"
        "- バックグラウンド活用: 3/3\n"
    )
    scores = _parse_personal_scores(text)
    assert scores["japan_demand"] == 2
    assert scores["solo_customer"] == 3
    assert scores["revenue_6mo"] == 1
    assert scores["background_fit"] == 3


def test_parse_personal_scores_returns_none_when_missing():
    scores = _parse_personal_scores("スコアなしのテキスト")
    assert scores["japan_demand"] is None
    assert scores["solo_customer"] is None
    assert scores["revenue_6mo"] is None
    assert scores["background_fit"] is None


def test_parse_personal_scores_clamps_to_0_3():
    text = (
        "日本市場需要: 5/3\n"
        "初顧客獲得可能性: 0/3\n"
        "6ヶ月収益化: 3/3\n"
        "バックグラウンド活用: 2/3\n"
    )
    scores = _parse_personal_scores(text)
    assert scores["japan_demand"] == 3
    assert scores["solo_customer"] == 0
    assert scores["revenue_6mo"] == 3
    assert scores["background_fit"] == 2


def test_run_meeting_saves_personal_scores(tmp_path):
    conn = init_db(tmp_path / "test.db")
    _make_high_score_idea(conn)

    ceo_conclusion = (
        "全員の意見を踏まえ判断します。\n"
        "個人文脈スコア:\n"
        "- 日本市場需要: 3/3\n"
        "- 初顧客獲得可能性: 2/3\n"
        "- 6ヶ月収益化: 2/3\n"
        "- バックグラウンド活用: 3/3\n"
        "結論: 採用\n"
        "次のアクション:\n1. MVPを構築する"
    )

    turn_counter = {"n": 0}
    def fake_call_agent(role, idea, history):
        turn_counter["n"] += 1
        if role == "ceo" and turn_counter["n"] > 1:
            return ceo_conclusion
        return "テスト発言"

    with (
        patch("meeting.main.DB_PATH", tmp_path / "test.db"),
        patch("meeting.main.call_agent", side_effect=fake_call_agent),
        patch("meeting.main.create_github_issue", return_value="https://github.com/x/y/issues/1"),
        patch.dict("os.environ", {"GITHUB_REPOSITORY": "x/y", "GITHUB_TOKEN": "tok"}),
    ):
        run_meeting()

    row = conn.execute("SELECT * FROM meeting_sessions").fetchone()
    assert row["personal_japan_demand"] == 3
    assert row["personal_solo_customer"] == 2
    assert row["personal_revenue_6mo"] == 2
    assert row["personal_background_fit"] == 3
