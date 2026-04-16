"""Tests for meeting/github_issue.py — written before implementation (TDD)."""

from unittest.mock import patch

import pytest

from meeting.github_issue import create_github_issue


class _MockResponse:
    def __init__(self, status_code: int, json_data: dict):
        self.status_code = status_code
        self._json = json_data

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


def test_create_github_issue_returns_url():
    mock_resp = _MockResponse(201, {"html_url": "https://github.com/owner/repo/issues/42"})
    with patch("meeting.github_issue.requests.post", return_value=mock_resp):
        url = create_github_issue(
            repo="owner/repo",
            token="ghp_testtoken",
            title="[アイデア採用] テストアイデア",
            body="## 概要\nテスト",
        )
    assert url == "https://github.com/owner/repo/issues/42"


def test_create_github_issue_sends_correct_headers():
    mock_resp = _MockResponse(201, {"html_url": "https://github.com/owner/repo/issues/1"})
    with patch("meeting.github_issue.requests.post", return_value=mock_resp) as mock_post:
        create_github_issue(repo="owner/repo", token="ghp_testtoken", title="テスト", body="本文")
    headers = mock_post.call_args.kwargs["headers"]
    assert headers["Authorization"] == "Bearer ghp_testtoken"
    assert headers["Accept"] == "application/vnd.github+json"


def test_create_github_issue_sends_correct_payload():
    mock_resp = _MockResponse(201, {"html_url": "https://github.com/owner/repo/issues/1"})
    with patch("meeting.github_issue.requests.post", return_value=mock_resp) as mock_post:
        create_github_issue(repo="owner/repo", token="ghp_testtoken", title="タイトル", body="本文テキスト")
    json_payload = mock_post.call_args.kwargs["json"]
    assert json_payload["title"] == "タイトル"
    assert json_payload["body"] == "本文テキスト"


def test_create_github_issue_posts_to_correct_url():
    mock_resp = _MockResponse(201, {"html_url": "https://github.com/owner/repo/issues/1"})
    with patch("meeting.github_issue.requests.post", return_value=mock_resp) as mock_post:
        create_github_issue(repo="myorg/myrepo", token="ghp_testtoken", title="テスト", body="本文")
    assert mock_post.call_args.args[0] == "https://api.github.com/repos/myorg/myrepo/issues"


def test_create_github_issue_returns_empty_string_on_http_error():
    mock_resp = _MockResponse(403, {})
    with patch("meeting.github_issue.requests.post", return_value=mock_resp):
        url = create_github_issue(repo="owner/repo", token="bad_token", title="テスト", body="本文")
    assert url == ""


def test_create_github_issue_returns_empty_string_on_network_error():
    with patch("meeting.github_issue.requests.post", side_effect=Exception("network error")):
        url = create_github_issue(repo="owner/repo", token="ghp_testtoken", title="テスト", body="本文")
    assert url == ""
