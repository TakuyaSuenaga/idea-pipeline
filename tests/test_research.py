"""Tests for pipeline/research.py — written first (TDD)."""

import pytest
import requests

from pipeline.research import fetch_hackernews, fetch_reddit, fetch_rss, run_research


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _MockResponse:
    def __init__(self, json_data, status_code=200):
        self._json = json_data
        self.status_code = status_code

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(response=self)


class _MockFeedEntry:
    def __init__(self, title, link, summary=""):
        self.title = title
        self.link = link
        self.summary = summary


class _MockFeed:
    def __init__(self, entries, bozo=False):
        self.entries = entries
        self.bozo = bozo


# ---------------------------------------------------------------------------
# fetch_hackernews
# ---------------------------------------------------------------------------

def test_fetch_hackernews_returns_list_of_dicts(mocker):
    mock_get = mocker.patch("pipeline.research.requests.get")
    mock_get.side_effect = [
        _MockResponse([101, 102]),
        _MockResponse({"id": 101, "type": "story", "title": "SaaS tool", "url": "https://example.com/101", "score": 150}),
        _MockResponse({"id": 102, "type": "story", "title": "SEO guide", "url": "https://example.com/102", "score": 80}),
    ]
    results = fetch_hackernews(limit=2)
    assert len(results) == 2
    assert results[0]["source"] == "hackernews"
    assert results[0]["title"] == "SaaS tool"
    assert results[0]["score"] == 150


def test_fetch_hackernews_skips_non_story_items(mocker):
    mock_get = mocker.patch("pipeline.research.requests.get")
    mock_get.side_effect = [
        _MockResponse([201, 202]),
        _MockResponse({"id": 201, "type": "job", "title": "Job post", "score": 0}),
        _MockResponse({"id": 202, "type": "story", "title": "Real story", "url": "https://x.com", "score": 50}),
    ]
    results = fetch_hackernews(limit=2)
    assert len(results) == 1
    assert results[0]["title"] == "Real story"


def test_fetch_hackernews_handles_timeout(mocker):
    mocker.patch("pipeline.research.requests.get", side_effect=requests.Timeout)
    assert fetch_hackernews() == []


def test_fetch_hackernews_handles_connection_error(mocker):
    mocker.patch("pipeline.research.requests.get", side_effect=requests.ConnectionError)
    assert fetch_hackernews() == []


def test_fetch_hackernews_skips_individual_item_failures(mocker):
    """One bad item must not abort the whole batch."""
    mock_get = mocker.patch("pipeline.research.requests.get")
    mock_get.side_effect = [
        _MockResponse([301, 302]),
        requests.Timeout(),
        _MockResponse({"id": 302, "type": "story", "title": "Good story", "url": "https://x.com", "score": 10}),
    ]
    results = fetch_hackernews(limit=2)
    assert len(results) == 1
    assert results[0]["title"] == "Good story"


def test_fetch_hackernews_result_has_required_keys(mocker):
    mock_get = mocker.patch("pipeline.research.requests.get")
    mock_get.side_effect = [
        _MockResponse([401]),
        _MockResponse({"id": 401, "type": "story", "title": "X", "url": "https://x.com", "score": 5}),
    ]
    results = fetch_hackernews(limit=1)
    for key in ("source", "title", "url", "content", "score", "category"):
        assert key in results[0], f"Missing key: {key}"


# ---------------------------------------------------------------------------
# fetch_reddit
# ---------------------------------------------------------------------------

def _reddit_payload(posts):
    return {"data": {"children": [{"data": p} for p in posts]}}


def test_fetch_reddit_returns_normalized_items(mocker):
    mock_get = mocker.patch("pipeline.research.requests.get")
    mock_get.return_value = _MockResponse(
        _reddit_payload([
            {"title": "SaaS pricing tips", "url": "https://reddit.com/r/SaaS/1",
             "selftext": "body text", "score": 200, "subreddit": "SaaS"},
        ])
    )
    results = fetch_reddit("SaaS")
    assert len(results) == 1
    assert results[0]["source"] == "reddit_SaaS"
    assert results[0]["title"] == "SaaS pricing tips"
    assert results[0]["score"] == 200


def test_fetch_reddit_handles_429_rate_limit(mocker):
    mock_get = mocker.patch("pipeline.research.requests.get")
    mock_get.return_value = _MockResponse({}, status_code=429)
    assert fetch_reddit("SaaS") == []


def test_fetch_reddit_handles_connection_error(mocker):
    mocker.patch("pipeline.research.requests.get", side_effect=requests.ConnectionError)
    assert fetch_reddit("SEO") == []


def test_fetch_reddit_result_has_required_keys(mocker):
    mock_get = mocker.patch("pipeline.research.requests.get")
    mock_get.return_value = _MockResponse(
        _reddit_payload([
            {"title": "T", "url": "https://reddit.com/1", "selftext": "", "score": 1, "subreddit": "startups"},
        ])
    )
    results = fetch_reddit("startups")
    for key in ("source", "title", "url", "content", "score", "category"):
        assert key in results[0]


# ---------------------------------------------------------------------------
# fetch_rss
# ---------------------------------------------------------------------------

def test_fetch_rss_returns_normalized_items(mocker):
    entries = [
        _MockFeedEntry("AI startup news", "https://techcrunch.com/1", "Summary text"),
        _MockFeedEntry("SaaS market trends", "https://techcrunch.com/2", ""),
    ]
    mocker.patch("pipeline.research.feedparser.parse", return_value=_MockFeed(entries))
    results = fetch_rss("https://techcrunch.com/feed/", limit=2)
    assert len(results) == 2
    assert results[0]["title"] == "AI startup news"
    assert results[0]["url"] == "https://techcrunch.com/1"


def test_fetch_rss_respects_limit(mocker):
    entries = [_MockFeedEntry(f"Entry {i}", f"https://x.com/{i}") for i in range(10)]
    mocker.patch("pipeline.research.feedparser.parse", return_value=_MockFeed(entries))
    results = fetch_rss("https://x.com/feed/", limit=3)
    assert len(results) == 3


def test_fetch_rss_handles_bozo_feed_with_no_entries(mocker):
    mocker.patch(
        "pipeline.research.feedparser.parse",
        return_value=_MockFeed(entries=[], bozo=True),
    )
    assert fetch_rss("https://broken.com/feed/") == []


def test_fetch_rss_handles_exception(mocker):
    mocker.patch("pipeline.research.feedparser.parse", side_effect=Exception("network error"))
    assert fetch_rss("https://x.com/feed/") == []


def test_fetch_rss_result_has_required_keys(mocker):
    entries = [_MockFeedEntry("Title", "https://x.com/1", "content")]
    mocker.patch("pipeline.research.feedparser.parse", return_value=_MockFeed(entries))
    results = fetch_rss("https://x.com/feed/", limit=1)
    for key in ("source", "title", "url", "content", "score", "category"):
        assert key in results[0]


# ---------------------------------------------------------------------------
# run_research
# ---------------------------------------------------------------------------

def test_run_research_aggregates_all_sources(mocker):
    mocker.patch("pipeline.research.fetch_hackernews", return_value=[{"source": "hackernews", "title": "HN"}])
    mocker.patch(
        "pipeline.research.fetch_reddit",
        side_effect=lambda sub, **kw: [{"source": f"reddit_{sub}", "title": sub}],
    )
    mocker.patch("pipeline.research.fetch_rss", return_value=[{"source": "techcrunch_rss", "title": "TC"}])
    results = run_research()
    sources = {r["source"] for r in results}
    assert "hackernews" in sources
    assert "techcrunch_rss" in sources
    assert any(s.startswith("reddit_") for s in sources)


def test_run_research_returns_empty_list_when_all_fail(mocker):
    mocker.patch("pipeline.research.fetch_hackernews", return_value=[])
    mocker.patch("pipeline.research.fetch_reddit", return_value=[])
    mocker.patch("pipeline.research.fetch_rss", return_value=[])
    assert run_research() == []
