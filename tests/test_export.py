"""Tests for pipeline/export.py — written first (TDD)."""

import json
from datetime import datetime

import pytest

import pipeline.export as export_module
from pipeline.export import export_ideas, export_research


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sample_ideas() -> list[dict]:
    return [
        {
            "id": 1,
            "title": "SEO Audit SaaS",
            "description": "Automated SEO audit tool.",
            "target_market": "SMB owners",
            "why_now": "LLMs make it cheap",
            "revenue_model": "Subscription",
            "difficulty": "low",
            "category": "saas",
            "generated_at": "2026-04-14T03:00:00+00:00",
        }
    ]


def _sample_research() -> list[dict]:
    return [
        {
            "id": 1,
            "source": "hackernews",
            "title": "AI trend story",
            "url": "https://example.com/1",
            "content": "Content here",
            "score": 100,
            "category": "saas",
            "fetched_at": "2026-04-14T03:00:00+00:00",
        }
    ]


# ---------------------------------------------------------------------------
# export_ideas
# ---------------------------------------------------------------------------

def test_export_ideas_creates_ideas_json(tmp_path, monkeypatch):
    monkeypatch.setattr(export_module, "DOCS_DATA_DIR", tmp_path)
    export_ideas(_sample_ideas())
    assert (tmp_path / "ideas.json").exists()


def test_export_ideas_json_contains_ideas(tmp_path, monkeypatch):
    monkeypatch.setattr(export_module, "DOCS_DATA_DIR", tmp_path)
    export_ideas(_sample_ideas())
    data = json.loads((tmp_path / "ideas.json").read_text(encoding="utf-8"))
    assert data["count"] == 1
    assert data["ideas"][0]["title"] == "SEO Audit SaaS"


def test_export_ideas_json_has_exported_at(tmp_path, monkeypatch):
    monkeypatch.setattr(export_module, "DOCS_DATA_DIR", tmp_path)
    export_ideas(_sample_ideas())
    data = json.loads((tmp_path / "ideas.json").read_text(encoding="utf-8"))
    assert "exported_at" in data
    datetime.fromisoformat(data["exported_at"])  # must be valid ISO 8601


def test_export_ideas_handles_empty_list(tmp_path, monkeypatch):
    monkeypatch.setattr(export_module, "DOCS_DATA_DIR", tmp_path)
    export_ideas([])
    data = json.loads((tmp_path / "ideas.json").read_text(encoding="utf-8"))
    assert data["count"] == 0
    assert data["ideas"] == []


def test_export_ideas_creates_parent_dir_if_missing(tmp_path, monkeypatch):
    nested = tmp_path / "nested" / "data"
    monkeypatch.setattr(export_module, "DOCS_DATA_DIR", nested)
    export_ideas(_sample_ideas())
    assert (nested / "ideas.json").exists()


def test_export_ideas_writes_japanese_without_escape(tmp_path, monkeypatch):
    monkeypatch.setattr(export_module, "DOCS_DATA_DIR", tmp_path)
    ideas = [{
        "id": 1, "title": "アイデア", "description": "説明",
        "category": "saas", "generated_at": "2026-04-14T00:00:00+00:00",
    }]
    export_ideas(ideas)
    raw = (tmp_path / "ideas.json").read_text(encoding="utf-8")
    assert "アイデア" in raw  # must not be \uXXXX-escaped


# ---------------------------------------------------------------------------
# export_research
# ---------------------------------------------------------------------------

def test_export_research_creates_research_json(tmp_path, monkeypatch):
    monkeypatch.setattr(export_module, "DOCS_DATA_DIR", tmp_path)
    export_research(_sample_research())
    assert (tmp_path / "research.json").exists()


def test_export_research_json_contains_items(tmp_path, monkeypatch):
    monkeypatch.setattr(export_module, "DOCS_DATA_DIR", tmp_path)
    export_research(_sample_research())
    data = json.loads((tmp_path / "research.json").read_text(encoding="utf-8"))
    assert data["count"] == 1
    assert data["items"][0]["source"] == "hackernews"


def test_export_research_has_exported_at(tmp_path, monkeypatch):
    monkeypatch.setattr(export_module, "DOCS_DATA_DIR", tmp_path)
    export_research(_sample_research())
    data = json.loads((tmp_path / "research.json").read_text(encoding="utf-8"))
    assert "exported_at" in data
    datetime.fromisoformat(data["exported_at"])


def test_export_research_handles_empty_list(tmp_path, monkeypatch):
    monkeypatch.setattr(export_module, "DOCS_DATA_DIR", tmp_path)
    export_research([])
    data = json.loads((tmp_path / "research.json").read_text(encoding="utf-8"))
    assert data["count"] == 0
    assert data["items"] == []
