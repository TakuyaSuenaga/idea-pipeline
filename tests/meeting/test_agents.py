"""Tests for meeting/agents.py — written before implementation (TDD)."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from meeting.agents import AGENT_ROLES, CEO_ROLE, call_agent, load_agent_persona


# ---------------------------------------------------------------------------
# load_agent_persona
# ---------------------------------------------------------------------------

def test_load_agent_persona_returns_string(tmp_path, monkeypatch):
    agents_dir = tmp_path / ".claude" / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "ceo.md").write_text("あなたはCEOです。", encoding="utf-8")
    monkeypatch.setattr("meeting.agents.AGENTS_DIR", agents_dir)
    result = load_agent_persona("ceo")
    assert "あなたはCEO" in result


def test_load_agent_persona_raises_for_missing_role(tmp_path, monkeypatch):
    agents_dir = tmp_path / ".claude" / "agents"
    agents_dir.mkdir(parents=True)
    monkeypatch.setattr("meeting.agents.AGENTS_DIR", agents_dir)
    with pytest.raises(FileNotFoundError):
        load_agent_persona("nonexistent")


def test_all_roles_have_persona_files():
    """Ensure all expected .claude/agents/*.md files exist in the project."""
    project_root = Path(__file__).parent.parent.parent
    agents_dir = project_root / ".claude" / "agents"
    for role in [*AGENT_ROLES, CEO_ROLE]:
        persona_file = agents_dir / f"{role}.md"
        assert persona_file.exists(), f"Missing persona file: {persona_file}"


# ---------------------------------------------------------------------------
# call_agent
# ---------------------------------------------------------------------------

def _make_mock_response(text: str) -> MagicMock:
    msg = MagicMock()
    msg.content = [MagicMock(text=text)]
    return msg


def test_call_agent_returns_string(tmp_path, monkeypatch):
    agents_dir = tmp_path / ".claude" / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "planning.md").write_text("あなたは企画担当です。", encoding="utf-8")
    monkeypatch.setattr("meeting.agents.AGENTS_DIR", agents_dir)

    mock_client = MagicMock()
    mock_client.messages.create.return_value = _make_mock_response("企画観点: 賛成")

    with patch("meeting.agents._client", mock_client):
        idea = {"title": "テスト", "description": "説明", "eval_total": 8.0}
        result = call_agent("planning", idea, [])

    assert isinstance(result, str)
    assert len(result) > 0


def test_call_agent_includes_idea_title_in_prompt(tmp_path, monkeypatch):
    agents_dir = tmp_path / ".claude" / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "sales.md").write_text("あなたは営業担当です。", encoding="utf-8")
    monkeypatch.setattr("meeting.agents.AGENTS_DIR", agents_dir)

    mock_client = MagicMock()
    mock_client.messages.create.return_value = _make_mock_response("営業観点: 賛成")

    with patch("meeting.agents._client", mock_client):
        idea = {"title": "ユニークなアイデアXYZ", "description": "説明", "eval_total": 9.0}
        call_agent("sales", idea, [])

    call_args = mock_client.messages.create.call_args
    messages = call_args.kwargs["messages"]
    user_content = messages[-1]["content"]
    assert "ユニークなアイデアXYZ" in user_content


def test_call_agent_passes_history(tmp_path, monkeypatch):
    agents_dir = tmp_path / ".claude" / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "marketing.md").write_text("あなたはマーケ担当です。", encoding="utf-8")
    monkeypatch.setattr("meeting.agents.AGENTS_DIR", agents_dir)

    mock_client = MagicMock()
    mock_client.messages.create.return_value = _make_mock_response("マーケ観点: 賛成")

    history = [
        {"role": "user", "content": "議題: テスト"},
        {"role": "assistant", "content": "企画観点: 賛成"},
    ]

    with patch("meeting.agents._client", mock_client):
        idea = {"title": "テスト", "description": "説明", "eval_total": 8.0}
        call_agent("marketing", idea, history)

    call_args = mock_client.messages.create.call_args
    messages = call_args.kwargs["messages"]
    assert len(messages) > 1


def test_call_agent_returns_empty_string_on_api_error(tmp_path, monkeypatch):
    agents_dir = tmp_path / ".claude" / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "dev.md").write_text("あなたは開発担当です。", encoding="utf-8")
    monkeypatch.setattr("meeting.agents.AGENTS_DIR", agents_dir)

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = Exception("API error")

    with patch("meeting.agents._client", mock_client):
        idea = {"title": "テスト", "description": "説明", "eval_total": 8.0}
        result = call_agent("dev", idea, [])

    assert result == ""


# ---------------------------------------------------------------------------
# constants
# ---------------------------------------------------------------------------

def test_agent_roles_contains_expected_roles():
    assert "planning" in AGENT_ROLES
    assert "sales" in AGENT_ROLES
    assert "marketing" in AGENT_ROLES
    assert "dev" in AGENT_ROLES
    assert "ops" in AGENT_ROLES


def test_ceo_role_constant():
    assert CEO_ROLE == "ceo"
