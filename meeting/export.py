"""Export meeting sessions and transcripts to JSON for GitHub Pages."""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

MEETINGS_JSON_PATH = Path(__file__).parent.parent / "docs" / "data" / "meetings.json"


def export_meetings(conn: sqlite3.Connection) -> None:
    """Write all meeting sessions (with messages) to docs/data/meetings.json."""
    sessions_rows = conn.execute(
        """
        SELECT
            ms.id,
            ms.idea_id,
            si.title AS idea_title,
            ms.held_at,
            ms.conclusion,
            ms.github_issue_url
        FROM meeting_sessions ms
        JOIN startup_ideas si ON si.id = ms.idea_id
        ORDER BY ms.id DESC
        """
    ).fetchall()

    sessions = []
    for row in sessions_rows:
        session = dict(row)
        messages = conn.execute(
            """
            SELECT agent_role, turn, content, created_at
            FROM meeting_messages
            WHERE session_id = ?
            ORDER BY turn ASC
            """,
            (session["id"],),
        ).fetchall()
        session["messages"] = [dict(m) for m in messages]
        sessions.append(session)

    MEETINGS_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "count": len(sessions),
        "sessions": sessions,
    }
    MEETINGS_JSON_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
