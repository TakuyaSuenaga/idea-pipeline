"""GitHub Issue creation for adopted ideas."""

import requests


def create_github_issue(repo: str, token: str, title: str, body: str) -> str:
    """Create a GitHub Issue and return its HTML URL.

    Returns an empty string on any error so the meeting pipeline can continue.

    Args:
        repo:  Repository in "owner/repo" format.
        token: GitHub personal access token or GITHUB_TOKEN.
        title: Issue title.
        body:  Issue body (Markdown).
    """
    try:
        response = requests.post(
            f"https://api.github.com/repos/{repo}/issues",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            json={"title": title, "body": body},
            timeout=30,
        )
        response.raise_for_status()
        return response.json().get("html_url", "")
    except Exception:
        return ""
