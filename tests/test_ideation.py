"""Tests for pipeline/ideation.py — written first (TDD)."""

import json

import anthropic
import pytest

from pipeline.ideation import _parse_ideas_json, _validate_idea, generate_ideas


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_message(text: str, mocker):
    block = mocker.MagicMock()
    block.type = "text"
    block.text = text
    msg = mocker.MagicMock()
    msg.content = [block]
    return msg


def _sample_ideas_json() -> str:
    return json.dumps([
        {
            "title": "SEO Audit SaaS",
            "description": "Automated SEO audit tool for small businesses.",
            "target_market": "SMB website owners",
            "why_now": "LLMs can now parse and summarize technical SEO reports cheaply.",
            "revenue_model": "Monthly subscription $29/mo",
            "difficulty": "low",
            "category": "saas",
        }
    ])


def _sample_research() -> list[dict]:
    return [{"id": 1, "title": "AI and SEO", "source": "hackernews", "content": "..."}]


# ---------------------------------------------------------------------------
# _parse_ideas_json
# ---------------------------------------------------------------------------

def test_parse_ideas_json_parses_plain_json():
    result = _parse_ideas_json(_sample_ideas_json())
    assert len(result) == 1
    assert result[0]["title"] == "SEO Audit SaaS"


def test_parse_ideas_json_strips_markdown_fences():
    raw = f"```json\n{_sample_ideas_json()}\n```"
    assert len(_parse_ideas_json(raw)) == 1


def test_parse_ideas_json_strips_plain_code_fences():
    raw = f"```\n{_sample_ideas_json()}\n```"
    assert len(_parse_ideas_json(raw)) == 1


def test_parse_ideas_json_falls_back_to_regex_extraction():
    raw = f"Here are some ideas:\n{_sample_ideas_json()}\nHope this helps!"
    assert len(_parse_ideas_json(raw)) == 1


def test_parse_ideas_json_returns_empty_on_invalid_json():
    assert _parse_ideas_json("this is not json at all") == []


def test_parse_ideas_json_returns_empty_on_non_array():
    assert _parse_ideas_json('{"key": "value"}') == []


# ---------------------------------------------------------------------------
# _validate_idea
# ---------------------------------------------------------------------------

def test_validate_idea_accepts_valid_idea():
    idea = {
        "title": "T", "description": "D", "category": "saas",
        "difficulty": "low", "target_market": "X", "why_now": "Y", "revenue_model": "Z",
    }
    assert _validate_idea(idea) is not None


def test_validate_idea_rejects_missing_title():
    assert _validate_idea({"description": "D", "category": "saas"}) is None


def test_validate_idea_rejects_missing_description():
    assert _validate_idea({"title": "T", "category": "saas"}) is None


def test_validate_idea_rejects_missing_category():
    assert _validate_idea({"title": "T", "description": "D"}) is None


def test_validate_idea_normalizes_invalid_difficulty():
    idea = {"title": "T", "description": "D", "category": "saas", "difficulty": "extreme"}
    assert _validate_idea(idea)["difficulty"] == "medium"


def test_validate_idea_normalizes_invalid_category():
    idea = {"title": "T", "description": "D", "category": "unknown"}
    assert _validate_idea(idea)["category"] == "saas"


# ---------------------------------------------------------------------------
# generate_ideas
# ---------------------------------------------------------------------------

def test_generate_ideas_returns_list_of_dicts(mocker):
    mock_client_cls = mocker.patch("pipeline.ideation.anthropic.Anthropic")
    mock_client_cls.return_value.messages.create.return_value = _make_mock_message(
        _sample_ideas_json(), mocker
    )
    results = generate_ideas(_sample_research())
    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0]["title"] == "SEO Audit SaaS"


def test_generate_ideas_calls_messages_create(mocker):
    mock_client_cls = mocker.patch("pipeline.ideation.anthropic.Anthropic")
    mock_client = mock_client_cls.return_value
    mock_client.messages.create.return_value = _make_mock_message(_sample_ideas_json(), mocker)
    generate_ideas(_sample_research())
    assert mock_client.messages.create.called


def test_generate_ideas_system_prompt_contains_skill_principles(mocker):
    mock_client_cls = mocker.patch("pipeline.ideation.anthropic.Anthropic")
    mock_client = mock_client_cls.return_value
    mock_client.messages.create.return_value = _make_mock_message(_sample_ideas_json(), mocker)
    generate_ideas(_sample_research())

    call_kwargs = mock_client.messages.create.call_args.kwargs
    system_content = " ".join(
        block["text"] for block in call_kwargs["system"] if block.get("type") == "text"
    )
    assert "tarpit" in system_content.lower() or "saas" in system_content.lower()


def test_generate_ideas_uses_cache_control(mocker):
    mock_client_cls = mocker.patch("pipeline.ideation.anthropic.Anthropic")
    mock_client = mock_client_cls.return_value
    mock_client.messages.create.return_value = _make_mock_message(_sample_ideas_json(), mocker)
    generate_ideas(_sample_research())

    call_kwargs = mock_client.messages.create.call_args.kwargs
    has_cache = any("cache_control" in block for block in call_kwargs["system"])
    assert has_cache, "System prompt must use cache_control for prompt caching"


def test_generate_ideas_returns_empty_on_api_status_error(mocker):
    mock_client_cls = mocker.patch("pipeline.ideation.anthropic.Anthropic")
    mock_response = mocker.MagicMock()
    mock_response.status_code = 500
    mock_client_cls.return_value.messages.create.side_effect = anthropic.APIStatusError(
        "Server error", response=mock_response, body={}
    )
    assert generate_ideas(_sample_research()) == []


def test_generate_ideas_returns_empty_on_connection_error(mocker):
    mock_client_cls = mocker.patch("pipeline.ideation.anthropic.Anthropic")
    mock_client_cls.return_value.messages.create.side_effect = anthropic.APIConnectionError(
        request=mocker.MagicMock()
    )
    assert generate_ideas(_sample_research()) == []


def test_generate_ideas_returns_empty_on_malformed_json(mocker):
    mock_client_cls = mocker.patch("pipeline.ideation.anthropic.Anthropic")
    mock_client_cls.return_value.messages.create.return_value = _make_mock_message(
        "not valid json", mocker
    )
    assert generate_ideas(_sample_research()) == []


def test_generate_ideas_returns_empty_when_no_research(mocker):
    mock_client_cls = mocker.patch("pipeline.ideation.anthropic.Anthropic")
    assert generate_ideas([]) == []
    mock_client_cls.return_value.messages.create.assert_not_called()
