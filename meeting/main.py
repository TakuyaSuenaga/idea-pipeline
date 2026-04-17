"""Entry point for the AI idea evaluation meeting.

Orchestrates a simulated board meeting where each agent evaluates a startup
idea from their domain perspective. The CEO synthesises all opinions and
decides whether to adopt or reject the idea. Adopted ideas become GitHub Issues.
"""

import os
from datetime import datetime, timezone

from pipeline.db import DB_PATH, init_db
from meeting.agents import AGENT_ROLES, CEO_ROLE, call_agent
from meeting.db import (
    add_meeting_message,
    create_meeting_session,
    get_ideas_for_meeting,
    update_meeting_conclusion,
)
from meeting.export import export_meetings
from meeting.github_issue import create_github_issue

MIN_SCORE = 7.0
MAX_IDEAS_PER_RUN = 3


def _build_issue_body(idea: dict, worker_messages: list[dict], conclusion_text: str) -> str:
    """Compose the GitHub Issue body from the meeting transcript."""
    held_at_jst = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    role_labels = {
        "planning": "企画担当",
        "sales": "営業担当",
        "marketing": "マーケティング担当",
        "dev": "開発担当",
        "ops": "運用担当",
    }

    worker_sections = ""
    for msg in worker_messages:
        role = msg.get("role", "")
        label = role_labels.get(role, role)
        worker_sections += f"### {label}\n{msg.get('content', '')}\n\n"

    return (
        f"## 概要\n{idea.get('description', '')}\n\n"
        f"## スコア\n"
        f"総合: **{idea.get('eval_total', 'N/A')}** / 10  \n"
        f"市場タイミング: {idea.get('eval_why_now', 'N/A')} | "
        f"差別化: {idea.get('eval_differentiation', 'N/A')} | "
        f"実現可能性: {idea.get('eval_feasibility', 'N/A')} | "
        f"市場規模: {idea.get('eval_market_size', 'N/A')}\n\n"
        f"## 会議の結論\n{conclusion_text}\n\n"
        f"## 各担当の意見\n{worker_sections}"
        f"---\n*会議日時: {held_at_jst}*"
    )


def _parse_conclusion(text: str) -> str:
    """Extract '採用' or '見送り' from the CEO's conclusion text.

    The CEO persona outputs '結論: 採用' or '結論: 見送り' as a structured marker.
    Matching on the full phrase avoids false positives from substrings like
    '採用できません' that appear in rejection reasoning.
    """
    if "結論: 採用" in text:
        return "採用"
    return "見送り"


def _run_idea_meeting(conn, idea: dict, repo: str, token: str) -> None:
    """Run a full meeting for one idea and persist the result."""
    session_id = create_meeting_session(conn, idea["id"])
    history: list[dict] = []
    turn = 0

    # CEO opens the meeting
    ceo_intro = call_agent(CEO_ROLE, idea, history)
    add_meeting_message(conn, session_id, CEO_ROLE, turn, ceo_intro)
    history.append({"role": "assistant", "content": ceo_intro})
    turn += 1

    # Each worker gives their opinion
    worker_messages: list[dict] = []
    for role in AGENT_ROLES:
        opinion = call_agent(role, idea, history)
        add_meeting_message(conn, session_id, role, turn, opinion)
        history.append({"role": "user", "content": f"[{role}] {opinion}"})
        worker_messages.append({"role": role, "content": opinion})
        turn += 1

    # CEO synthesises and decides
    conclusion_text = call_agent(CEO_ROLE, idea, history)
    add_meeting_message(conn, session_id, CEO_ROLE, turn, conclusion_text)
    conclusion = _parse_conclusion(conclusion_text)

    issue_url = ""
    if conclusion == "採用" and repo and token:
        body = _build_issue_body(idea, worker_messages, conclusion_text)
        issue_url = create_github_issue(
            repo=repo,
            token=token,
            title=f"[アイデア採用] {idea['title']}",
            body=body,
        )

    update_meeting_conclusion(conn, session_id, conclusion, issue_url or None)
    print(
        f"[meeting] idea={idea['id']} '{idea['title']}' → {conclusion}"
        + (f"  {issue_url}" if issue_url else "")
    )


def run_meeting() -> None:
    """Main entry point: evaluate all pending high-score ideas."""
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    token = os.environ.get("GITHUB_TOKEN", "")

    conn = init_db(DB_PATH)
    ideas = get_ideas_for_meeting(conn, min_score=MIN_SCORE, limit=MAX_IDEAS_PER_RUN)

    if not ideas:
        print("[meeting] No new ideas to discuss today.")
    else:
        print(f"[meeting] Starting meeting for {len(ideas)} idea(s).")
        for idea in ideas:
            try:
                _run_idea_meeting(conn, idea, repo, token)
            except Exception as exc:
                print(f"[meeting] ERROR processing idea {idea.get('id')}: {exc}")

    try:
        export_meetings(conn)
        print("[meeting] Exported meetings.json.")
    except Exception as exc:
        print(f"[meeting] WARNING: Failed to export meetings.json: {exc}")


if __name__ == "__main__":
    run_meeting()
