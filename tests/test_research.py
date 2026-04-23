"""Tests for pipeline/research.py — written first (TDD)."""

import pytest
import requests

from pipeline.research import (
    fetch_github_trending,
    fetch_google_trends_jp,
    fetch_hackernews,
    fetch_producthunt,
    fetch_prtimes,
    fetch_qiita_trending,
    fetch_reddit,
    fetch_rss,
    run_research,
)


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
# fetch_producthunt
# ---------------------------------------------------------------------------

def test_fetch_producthunt_returns_normalized_items(mocker):
    entries = [
        _MockFeedEntry("ProductX — AI todo app", "https://www.producthunt.com/posts/productx", "An AI-powered todo app."),
        _MockFeedEntry("ProductY — SEO toolkit", "https://www.producthunt.com/posts/producty", ""),
    ]
    mocker.patch("pipeline.research.feedparser.parse", return_value=_MockFeed(entries))
    results = fetch_producthunt(limit=2)
    assert len(results) == 2
    assert results[0]["source"] == "producthunt"
    assert results[0]["title"] == "ProductX — AI todo app"
    assert results[0]["url"] == "https://www.producthunt.com/posts/productx"


def test_fetch_producthunt_respects_limit(mocker):
    entries = [_MockFeedEntry(f"P{i}", f"https://ph.com/{i}") for i in range(10)]
    mocker.patch("pipeline.research.feedparser.parse", return_value=_MockFeed(entries))
    assert len(fetch_producthunt(limit=3)) == 3


def test_fetch_producthunt_handles_exception(mocker):
    mocker.patch("pipeline.research.feedparser.parse", side_effect=Exception("network error"))
    assert fetch_producthunt() == []


def test_fetch_producthunt_handles_bozo_feed_with_no_entries(mocker):
    mocker.patch(
        "pipeline.research.feedparser.parse",
        return_value=_MockFeed(entries=[], bozo=True),
    )
    assert fetch_producthunt() == []


def test_fetch_producthunt_result_has_required_keys(mocker):
    entries = [_MockFeedEntry("Title", "https://ph.com/1", "summary")]
    mocker.patch("pipeline.research.feedparser.parse", return_value=_MockFeed(entries))
    results = fetch_producthunt(limit=1)
    for key in ("source", "title", "url", "content", "score", "category"):
        assert key in results[0]


# ---------------------------------------------------------------------------
# fetch_github_trending
# ---------------------------------------------------------------------------

def _gh_payload(repos):
    return {"items": repos}


def test_fetch_github_trending_returns_normalized_items(mocker):
    mock_get = mocker.patch("pipeline.research.requests.get")
    mock_get.return_value = _MockResponse(
        _gh_payload([
            {
                "full_name": "foo/saas-boilerplate",
                "description": "A SaaS boilerplate.",
                "html_url": "https://github.com/foo/saas-boilerplate",
                "stargazers_count": 500,
            },
        ])
    )
    results = fetch_github_trending(limit=1)
    assert len(results) == 1
    assert results[0]["source"] == "github_trending"
    assert results[0]["title"] == "foo/saas-boilerplate"
    assert results[0]["score"] == 500
    assert results[0]["url"] == "https://github.com/foo/saas-boilerplate"


def test_fetch_github_trending_handles_403_rate_limit(mocker):
    mock_get = mocker.patch("pipeline.research.requests.get")
    mock_get.return_value = _MockResponse({}, status_code=403)
    assert fetch_github_trending() == []


def test_fetch_github_trending_handles_connection_error(mocker):
    mocker.patch("pipeline.research.requests.get", side_effect=requests.ConnectionError)
    assert fetch_github_trending() == []


def test_fetch_github_trending_skips_items_without_name(mocker):
    mock_get = mocker.patch("pipeline.research.requests.get")
    mock_get.return_value = _MockResponse(
        _gh_payload([
            {"description": "No full_name", "html_url": "https://github.com/x", "stargazers_count": 10},
            {"full_name": "ok/repo", "description": "OK", "html_url": "https://github.com/ok/repo", "stargazers_count": 20},
        ])
    )
    results = fetch_github_trending(limit=2)
    assert len(results) == 1
    assert results[0]["title"] == "ok/repo"


def test_fetch_github_trending_result_has_required_keys(mocker):
    mock_get = mocker.patch("pipeline.research.requests.get")
    mock_get.return_value = _MockResponse(
        _gh_payload([
            {"full_name": "a/b", "description": "", "html_url": "https://github.com/a/b", "stargazers_count": 1},
        ])
    )
    results = fetch_github_trending(limit=1)
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
    mocker.patch("pipeline.research.fetch_producthunt", return_value=[{"source": "producthunt", "title": "PH"}])
    mocker.patch("pipeline.research.fetch_github_trending", return_value=[{"source": "github_trending", "title": "GH"}])
    mocker.patch("pipeline.research.fetch_prtimes", return_value=[{"source": "prtimes", "title": "PT"}])
    mocker.patch("pipeline.research.fetch_qiita_trending", return_value=[{"source": "qiita_trending", "title": "QT"}])
    mocker.patch("pipeline.research.fetch_google_trends_jp", return_value=[{"source": "google_trends_jp", "title": "GT"}])
    results = run_research()
    sources = {r["source"] for r in results}
    assert "hackernews" in sources
    assert "techcrunch_rss" in sources
    assert "producthunt" in sources
    assert "github_trending" in sources
    assert any(s.startswith("reddit_") for s in sources)
    assert "prtimes" in sources
    assert "qiita_trending" in sources
    assert "google_trends_jp" in sources


def test_run_research_returns_empty_list_when_all_fail(mocker):
    mocker.patch("pipeline.research.fetch_hackernews", return_value=[])
    mocker.patch("pipeline.research.fetch_reddit", return_value=[])
    mocker.patch("pipeline.research.fetch_rss", return_value=[])
    mocker.patch("pipeline.research.fetch_producthunt", return_value=[])
    mocker.patch("pipeline.research.fetch_github_trending", return_value=[])
    mocker.patch("pipeline.research.fetch_prtimes", return_value=[])
    mocker.patch("pipeline.research.fetch_qiita_trending", return_value=[])
    mocker.patch("pipeline.research.fetch_google_trends_jp", return_value=[])
    assert run_research() == []


# ---------------------------------------------------------------------------
# fetch_prtimes
# ---------------------------------------------------------------------------

def test_fetch_prtimes_returns_prtimes_source(mocker):
    entries = [_MockFeedEntry("スタートアップ新製品発表", "https://prtimes.jp/main/1", "概要テキスト")]
    mocker.patch("pipeline.research.feedparser.parse", return_value=_MockFeed(entries))
    results = fetch_prtimes(limit=1)
    assert len(results) == 1
    assert results[0]["source"] == "prtimes"
    assert results[0]["title"] == "スタートアップ新製品発表"


def test_fetch_prtimes_handles_exception(mocker):
    mocker.patch("pipeline.research.feedparser.parse", side_effect=Exception("network error"))
    assert fetch_prtimes() == []


def test_fetch_prtimes_respects_limit(mocker):
    entries = [_MockFeedEntry(f"PR{i}", f"https://prtimes.jp/{i}") for i in range(10)]
    mocker.patch("pipeline.research.feedparser.parse", return_value=_MockFeed(entries))
    assert len(fetch_prtimes(limit=3)) == 3


# ---------------------------------------------------------------------------
# fetch_qiita_trending
# ---------------------------------------------------------------------------

def test_fetch_qiita_trending_returns_qiita_source(mocker):
    entries = [_MockFeedEntry("Qiitaトレンド記事", "https://qiita.com/items/1", "内容")]
    mocker.patch("pipeline.research.feedparser.parse", return_value=_MockFeed(entries))
    results = fetch_qiita_trending(limit=1)
    assert len(results) == 1
    assert results[0]["source"] == "qiita_trending"
    assert results[0]["title"] == "Qiitaトレンド記事"


def test_fetch_qiita_trending_handles_exception(mocker):
    mocker.patch("pipeline.research.feedparser.parse", side_effect=Exception("network error"))
    assert fetch_qiita_trending() == []


def test_fetch_qiita_trending_respects_limit(mocker):
    entries = [_MockFeedEntry(f"Article{i}", f"https://qiita.com/{i}") for i in range(10)]
    mocker.patch("pipeline.research.feedparser.parse", return_value=_MockFeed(entries))
    assert len(fetch_qiita_trending(limit=4)) == 4


# ---------------------------------------------------------------------------
# fetch_google_trends_jp
# ---------------------------------------------------------------------------

def test_fetch_google_trends_jp_returns_items(mocker):
    mock_df = mocker.MagicMock()
    mock_df.__getitem__.return_value.head.return_value = ["AI副業", "SaaS導入"]
    mock_req = mocker.MagicMock()
    mock_req.trending_searches.return_value = mock_df
    mocker.patch("pipeline.research._PYTRENDS_AVAILABLE", True)
    mocker.patch("pipeline.research._TrendReq", return_value=mock_req)
    results = fetch_google_trends_jp(limit=2)
    assert len(results) == 2
    assert results[0]["source"] == "google_trends_jp"
    assert results[0]["title"] == "AI副業"


def test_fetch_google_trends_jp_result_has_required_keys(mocker):
    mock_df = mocker.MagicMock()
    mock_df.__getitem__.return_value.head.return_value = ["フリーランス"]
    mock_req = mocker.MagicMock()
    mock_req.trending_searches.return_value = mock_df
    mocker.patch("pipeline.research._PYTRENDS_AVAILABLE", True)
    mocker.patch("pipeline.research._TrendReq", return_value=mock_req)
    results = fetch_google_trends_jp(limit=1)
    for key in ("source", "title", "url", "content", "score", "category"):
        assert key in results[0]


def test_fetch_google_trends_jp_handles_exception(mocker):
    mocker.patch("pipeline.research._PYTRENDS_AVAILABLE", True)
    mocker.patch("pipeline.research._TrendReq", side_effect=Exception("rate limited"))
    assert fetch_google_trends_jp() == []


def test_fetch_google_trends_jp_returns_empty_when_unavailable(mocker):
    mocker.patch("pipeline.research._PYTRENDS_AVAILABLE", False)
    assert fetch_google_trends_jp() == []


# ---------------------------------------------------------------------------
# fetch_rss source_name parameter
# ---------------------------------------------------------------------------

def test_fetch_rss_uses_custom_source_name(mocker):
    entries = [_MockFeedEntry("Article", "https://example.com/1", "content")]
    mocker.patch("pipeline.research.feedparser.parse", return_value=_MockFeed(entries))
    results = fetch_rss("https://example.com/feed/", source_name="my_source", limit=1)
    assert results[0]["source"] == "my_source"
