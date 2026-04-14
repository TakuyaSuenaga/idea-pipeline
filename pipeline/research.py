"""Market research fetchers: Hacker News, Reddit, RSS feeds."""

import feedparser
import requests

_HN_BASE = "https://hacker-news.firebaseio.com/v0"
_REDDIT_HEADERS = {"User-Agent": "idea-pipeline/1.0 (automated market research)"}
_TECHCRUNCH_RSS = "https://techcrunch.com/feed/"

_SAAS_KEYWORDS = {"saas", "software", "api", "subscription", "b2b", "startup", "tool"}
_SEO_KEYWORDS = {"seo", "search", "ranking", "google", "keyword", "backlink", "traffic"}


def _assign_category(text: str) -> str:
    lower = text.lower()
    if any(k in lower for k in _SEO_KEYWORDS):
        return "seo"
    if any(k in lower for k in _SAAS_KEYWORDS):
        return "saas"
    return "general"


def fetch_hackernews(limit: int = 30) -> list[dict]:
    """Fetch top stories from Hacker News Firebase API."""
    try:
        resp = requests.get(f"{_HN_BASE}/topstories.json", timeout=10)
        resp.raise_for_status()
        story_ids: list[int] = resp.json()[:limit]
    except (requests.RequestException, ValueError):
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
                    "url": url or None,
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
    url = f"https://www.reddit.com/r/{subreddit}/top.json?limit={limit}&t=week"
    try:
        resp = requests.get(url, headers=_REDDIT_HEADERS, timeout=15)
        if resp.status_code == 429:
            return []
        resp.raise_for_status()
        posts = resp.json()["data"]["children"]
    except (requests.RequestException, ValueError, KeyError):
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
                "url": data.get("url"),
                "content": (data.get("selftext", "") or "")[:500] or None,
                "score": data.get("score"),
                "category": _assign_category(title),
            }
        )
    return items


def fetch_rss(url: str, limit: int = 20) -> list[dict]:
    """Fetch entries from an RSS feed."""
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
                    "source": "techcrunch_rss",
                    "title": title,
                    "url": getattr(entry, "link", None),
                    "content": (getattr(entry, "summary", "") or "")[:500] or None,
                    "score": None,
                    "category": _assign_category(title),
                }
            )
        return items
    except Exception:
        return []


def run_research() -> list[dict]:
    """Aggregate research from all sources and return combined list."""
    results: list[dict] = []
    results.extend(fetch_hackernews())
    for sub in ("SaaS", "SEO", "startups"):
        results.extend(fetch_reddit(sub))
    results.extend(fetch_rss(_TECHCRUNCH_RSS))
    return results
