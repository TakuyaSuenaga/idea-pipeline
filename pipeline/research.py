"""Market research fetchers: Hacker News, Reddit, RSS feeds, Product Hunt, GitHub Trending,
PRTIMES, Qiita Trending, Google Trends JP."""

import os
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import quote, urlparse

import feedparser
import requests

try:
    from pytrends.request import TrendReq as _TrendReq
    _PYTRENDS_AVAILABLE = True
except ImportError:
    _TrendReq = None
    _PYTRENDS_AVAILABLE = False

_HN_BASE = "https://hacker-news.firebaseio.com/v0"
_REDDIT_HEADERS = {"User-Agent": "idea-pipeline/1.0 (automated market research)"}
_TECHCRUNCH_RSS = "https://techcrunch.com/feed/"
_PRODUCTHUNT_RSS = "https://www.producthunt.com/feed"
_GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"
_GITHUB_HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "idea-pipeline/1.0 (automated market research)",
}
_PRTIMES_RSS = "https://prtimes.jp/rss2.0/"
_QIITA_TRENDING_RSS = "https://qiita.com/popular-items/feed.atom"

_SAAS_KEYWORDS = {"saas", "software", "api", "subscription", "b2b", "startup", "tool"}
_SEO_KEYWORDS = {"seo", "search", "ranking", "google", "keyword", "backlink", "traffic"}
_SUBREDDIT_RE = re.compile(r"^[A-Za-z0-9_]{1,50}$")


def _assign_category(text: str) -> str:
    lower = text.lower()
    if any(k in lower for k in _SEO_KEYWORDS):
        return "seo"
    if any(k in lower for k in _SAAS_KEYWORDS):
        return "saas"
    return "general"


def _safe_url(url: str | None) -> str | None:
    """Return the URL if scheme is http(s); else None. Blocks javascript:/data: etc."""
    if not url or not isinstance(url, str):
        return None
    try:
        parsed = urlparse(url)
    except ValueError:
        return None
    if parsed.scheme in ("http", "https") and parsed.netloc:
        return url
    return None


def _github_headers() -> dict:
    """GitHub request headers with optional bearer token for higher rate limit."""
    headers = dict(_GITHUB_HEADERS)
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def fetch_hackernews(limit: int = 30) -> list[dict]:
    """Fetch top stories from Hacker News Firebase API."""
    try:
        resp = requests.get(f"{_HN_BASE}/topstories.json", timeout=10)
        resp.raise_for_status()
        story_ids: list[int] = resp.json()[:limit]
    except (requests.RequestException, ValueError) as exc:
        print(f"[research] Hacker News fetch failed: {exc}")
        return []

    items = []
    for story_id in story_ids:
        try:
            r = requests.get(f"{_HN_BASE}/item/{story_id}.json", timeout=5)
            r.raise_for_status()
            item = r.json()
            if not item or item.get("type") != "story" or not item.get("title"):
                continue
            title = item["title"]
            url = item.get("url", "")
            items.append(
                {
                    "source": "hackernews",
                    "title": title,
                    "url": _safe_url(url) if url else None,
                    "content": item.get("text", "")[:500] or None,
                    "score": item.get("score"),
                    "category": _assign_category(title),
                }
            )
        except (requests.RequestException, ValueError):
            continue

    return items


def fetch_reddit(subreddit: str, limit: int = 25) -> list[dict]:
    """Fetch top posts from a subreddit using the public JSON API."""
    if not _SUBREDDIT_RE.match(subreddit or ""):
        print(f"[research] Reddit fetch rejected: invalid subreddit '{subreddit}'")
        return []
    safe_sub = quote(subreddit, safe="")
    url = f"https://www.reddit.com/r/{safe_sub}/top.json"
    try:
        resp = requests.get(
            url,
            headers=_REDDIT_HEADERS,
            params={"limit": limit, "t": "week"},
            timeout=15,
        )
        if resp.status_code == 429:
            print(f"[research] Reddit rate limited (429) for r/{subreddit}")
            return []
        resp.raise_for_status()
        posts = resp.json()["data"]["children"]
    except (requests.RequestException, ValueError, KeyError) as exc:
        print(f"[research] Reddit fetch failed for r/{subreddit}: {exc}")
        return []

    items = []
    for post in posts:
        data = post.get("data", {})
        title = data.get("title", "")
        if not title:
            continue
        items.append(
            {
                "source": f"reddit_{subreddit}",
                "title": title,
                "url": _safe_url(data.get("url")),
                "content": (data.get("selftext", "") or "")[:500] or None,
                "score": data.get("score"),
                "category": _assign_category(title),
            }
        )
    return items


def fetch_rss(url: str, source_name: str = "rss", limit: int = 20) -> list[dict]:
    """Fetch entries from an RSS/Atom feed."""
    try:
        feed = feedparser.parse(url)
        if feed.bozo and not feed.entries:
            return []
        items = []
        for entry in feed.entries[:limit]:
            title = getattr(entry, "title", "") or ""
            if not title:
                continue
            items.append(
                {
                    "source": source_name,
                    "title": title,
                    "url": _safe_url(getattr(entry, "link", None)),
                    "content": (getattr(entry, "summary", "") or "")[:500] or None,
                    "score": None,
                    "category": _assign_category(title),
                }
            )
        return items
    except Exception as exc:
        print(f"[research] RSS fetch failed for {url}: {exc}")
        return []


def fetch_producthunt(limit: int = 20) -> list[dict]:
    """Fetch recent launches from Product Hunt RSS."""
    try:
        feed = feedparser.parse(_PRODUCTHUNT_RSS)
        if feed.bozo and not feed.entries:
            return []
        items = []
        for entry in feed.entries[:limit]:
            title = getattr(entry, "title", "") or ""
            if not title:
                continue
            items.append(
                {
                    "source": "producthunt",
                    "title": title,
                    "url": _safe_url(getattr(entry, "link", None)),
                    "content": (getattr(entry, "summary", "") or "")[:500] or None,
                    "score": None,
                    "category": _assign_category(title),
                }
            )
        return items
    except Exception as exc:
        print(f"[research] Product Hunt fetch failed: {exc}")
        return []


def fetch_github_trending(limit: int = 25) -> list[dict]:
    """Fetch recently created high-star repos from GitHub (trending proxy)."""
    since = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
    params = {
        "q": f"created:>{since} stars:>50",
        "sort": "stars",
        "order": "desc",
        "per_page": limit,
    }
    try:
        resp = requests.get(
            _GITHUB_SEARCH_URL,
            headers=_github_headers(),
            params=params,
            timeout=15,
        )
        if resp.status_code in (403, 429):
            print(f"[research] GitHub API rate limited ({resp.status_code})")
            return []
        resp.raise_for_status()
        repos = resp.json().get("items", [])
        items = []
        for repo in repos:
            full_name = repo.get("full_name")
            if not full_name:
                continue
            description = repo.get("description") or ""
            items.append(
                {
                    "source": "github_trending",
                    "title": full_name,
                    "url": _safe_url(repo.get("html_url")),
                    "content": description[:500] or None,
                    "score": repo.get("stargazers_count"),
                    "category": _assign_category(f"{full_name} {description}"),
                }
            )
        return items
    except (requests.RequestException, ValueError, AttributeError) as exc:
        print(f"[research] GitHub trending fetch failed: {exc}")
        return []


def fetch_prtimes(limit: int = 10) -> list[dict]:
    """PRTIMESの最新プレスリリースをRSSから取得する（日本の市場動向シグナル）。"""
    return fetch_rss(_PRTIMES_RSS, source_name="prtimes", limit=limit)


def fetch_qiita_trending(limit: int = 10) -> list[dict]:
    """Qiitaの人気記事をRSSから取得する（日本のエンジニア技術トレンド）。"""
    return fetch_rss(_QIITA_TRENDING_RSS, source_name="qiita_trending", limit=limit)


def fetch_google_trends_jp(limit: int = 10) -> list[dict]:
    """Google Trendsの日本トレンド検索キーワードを取得する。

    pytrends が未インストールの場合や Google 側のレート制限時は空リストを返す。
    """
    if not _PYTRENDS_AVAILABLE:
        print("[research] Google Trends: pytrends not installed, skipping")
        return []
    try:
        req = _TrendReq(hl="ja", tz=540, timeout=(10, 25))
        trending_df = req.trending_searches(pn="japan")
        items = []
        for keyword in list(trending_df[0].head(limit)):
            keyword_str = str(keyword)
            items.append(
                {
                    "source": "google_trends_jp",
                    "title": keyword_str,
                    "url": None,
                    "content": f"日本のGoogleトレンド検索: {keyword_str}",
                    "score": None,
                    "category": _assign_category(keyword_str),
                }
            )
        return items
    except Exception as exc:
        print(f"[research] Google Trends JP fetch failed: {exc}")
        return []


def run_research() -> list[dict]:
    """Aggregate research from all sources and return combined list.

    英語圏ソースは各5件に絞り、日本ソース（PRTIMES・Qiita・Google Trends）を追加する。
    """
    results: list[dict] = []
    # English sources — top 5 each to avoid overwhelming JP signal
    results.extend(fetch_hackernews(limit=5))
    for sub in ("SaaS", "SEO", "startups"):
        results.extend(fetch_reddit(sub, limit=5))
    results.extend(fetch_rss(_TECHCRUNCH_RSS, source_name="techcrunch_rss", limit=5))
    results.extend(fetch_producthunt(limit=5))
    results.extend(fetch_github_trending(limit=5))
    # Japanese sources
    results.extend(fetch_prtimes())
    results.extend(fetch_qiita_trending())
    results.extend(fetch_google_trends_jp())
    return results
