"""Database operations for the AI meeting system."""

import sqlite3


def get_ideas_for_meeting(
    conn: sqlite3.Connection,
    min_score: float = 7.0,
    limit: int = 3,
) -> list[dict]:
    """Return high-scoring ideas that have not yet been discussed.

    Ideas are ordered by eval_total descending so the best ideas are
    discussed first.
    """
    cursor = conn.execute(
        """
        SELECT s.*
        FROM startup_ideas s
        LEFT JOIN meeting_sessions m ON m.idea_id = s.id
        WHERE s.eval_total >= ?
          AND m.id IS NULL
        ORDER BY s.eval_total DESC
        LIMIT ?
        """,
        (min_score, limit),
    )
    return [dict(row) for row in cursor.fetchall()]


def create_meeting_session(conn: sqlite3.Connection, idea_id: int) -> int:
    """Insert a new meeting session row and return its id."""
    cursor = conn.execute(
        "INSERT INTO meeting_sessions (idea_id) VALUES (?)",
        (idea_id,),
    )
    conn.commit()
    return cursor.lastrowid


def add_meeting_message(
    conn: sqlite3.Connection,
    session_id: int,
    agent_role: str,
    turn: int,
    content: str,
) -> int:
    """Append one agent message to the meeting transcript and return its id."""
    cursor = conn.execute(
        """
        INSERT INTO meeting_messages (session_id, agent_role, turn, content)
        VALUES (?, ?, ?, ?)
        """,
        (session_id, agent_role, turn, content),
    )
    conn.commit()
    return cursor.lastrowid


def update_meeting_conclusion(
    conn: sqlite3.Connection,
    session_id: int,
    conclusion: str,
    github_issue_url: str | None = None,
) -> None:
    """Record the final conclusion (and optional issue URL) for a session."""
    conn.execute(
        """
        UPDATE meeting_sessions
        SET conclusion = ?, github_issue_url = ?
        WHERE id = ?
        """,
        (conclusion, github_issue_url, session_id),
    )
    conn.commit()


def update_personal_scores(
    conn: sqlite3.Connection,
    session_id: int,
    japan_demand: int | None,
    solo_customer: int | None,
    revenue_6mo: int | None,
    background_fit: int | None,
) -> None:
    """Record personal context scores (0-3 each) for a meeting session."""
    conn.execute(
        """
        UPDATE meeting_sessions
        SET personal_japan_demand = ?,
            personal_solo_customer = ?,
            personal_revenue_6mo = ?,
            personal_background_fit = ?
        WHERE id = ?
        """,
        (japan_demand, solo_customer, revenue_6mo, background_fit, session_id),
    )
    conn.commit()
