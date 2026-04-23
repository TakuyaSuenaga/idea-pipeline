"""Entry point for the AI idea evaluation meeting.

Orchestrates a simulated board meeting where each agent evaluates a startup
idea from their domain perspective. The CEO synthesises all opinions and
decides whether to adopt or reject the idea. Adopted ideas become GitHub Issues.
"""

import os
import re
from datetime import datetime, timezone

from pipeline.db import DB_PATH, init_db
from meeting.agents import AGENT_ROLES, CEO_ROLE, call_agent
from meeting.db import (
    add_meeting_message,
    create_meeting_session,
    get_ideas_for_meeting,
    update_meeting_conclusion,
    update_personal_scores,
)
from meeting.export import export_meetings
from meeting.github_issue import create_github_issue

MIN_SCORE = 7.0
MAX_IDEAS_PER_RUN = 3

# 「結論: 採用」を Markdown 太字・全角コロン・空白ゆらぎに耐えて検出する。
# '採用できません' のような substring に誤マッチしないよう、先頭の '結論[:：]' を必須にする。
_ADOPT_RE = re.compile(r"結論\**\s*[:：]\s*\**\s*採用")

_PERSONAL_JP_DEMAND_RE = re.compile(r"日本市場需要[^\d]*(\d{1,2})/3")
_PERSONAL_SOLO_CUSTOMER_RE = re.compile(r"初顧客獲得可能性[^\d]*(\d{1,2})/3")
_PERSONAL_REVENUE_RE = re.compile(r"6ヶ月収益化[^\d]*(\d{1,2})/3")
_PERSONAL_BG_FIT_RE = re.compile(r"バックグラウンド活用[^\d]*(\d{1,2})/3")


def _build_issue_body(
    idea: dict,
    worker_messages: list[dict],
    conclusion_text: str,
    personal_scores: dict[str, int | None],
) -> str:
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

    def _score(v: int | None) -> str:
        return str(v) if v is not None else "N/A"

    personal_section = (
        f"## 個人文脈スコア（Takuya向け）\n"
        f"日本市場需要: **{_score(personal_scores.get('japan_demand'))}/3** | "
        f"初顧客獲得可能性: **{_score(personal_scores.get('solo_customer'))}/3** | "
        f"6ヶ月収益化: **{_score(personal_scores.get('revenue_6mo'))}/3** | "
        f"バックグラウンド活用: **{_score(personal_scores.get('background_fit'))}/3**\n\n"
    )

    return (
        f"## 概要\n{idea.get('description', '')}\n\n"
        f"## スコア\n"
        f"総合: **{idea.get('eval_total', 'N/A')}** / 10  \n"
        f"市場タイミング: {idea.get('eval_why_now', 'N/A')} | "
        f"差別化: {idea.get('eval_differentiation', 'N/A')} | "
        f"実現可能性: {idea.get('eval_feasibility', 'N/A')} | "
        f"市場規模: {idea.get('eval_market_size', 'N/A')} | "
        f"Pain Point: {idea.get('eval_pain_point', 'N/A')}\n\n"
        f"{personal_section}"
        f"## 会議の結論\n{conclusion_text}\n\n"
        f"## 各担当の意見\n{worker_sections}"
        f"---\n*会議日時: {held_at_jst}*"
    )


def _parse_conclusion(text: str) -> str:
    """Extract '採用' or '見送り' from the CEO's conclusion text.

    The CEO persona outputs '結論: 採用' or '結論: 見送り' as a structured marker.
    LLM は強調のため Markdown 太字 (**採用**) や全角コロンを付与することがあるため
    正規表現で吸収する。'採用できません' 等の substring を拾わないよう、
    '結論[:：]' プレフィックス直後の「採用」のみを見る。
    """
    if _ADOPT_RE.search(text):
        return "採用"
    return "見送り"


def _clamp_personal_score(value: int) -> int:
    return max(0, min(3, value))


def _parse_personal_scores(text: str) -> dict[str, int | None]:
    """CEO結論テキストから個人文脈スコア（0-3）を抽出する。"""
    def _extract(pattern: re.Pattern) -> int | None:
        m = pattern.search(text)
        return _clamp_personal_score(int(m.group(1))) if m else None

    return {
        "japan_demand": _extract(_PERSONAL_JP_DEMAND_RE),
        "solo_customer": _extract(_PERSONAL_SOLO_CUSTOMER_RE),
        "revenue_6mo": _extract(_PERSONAL_REVENUE_RE),
        "background_fit": _extract(_PERSONAL_BG_FIT_RE),
    }


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
    personal_scores = _parse_personal_scores(conclusion_text)

    issue_url = ""
    if conclusion == "採用" and repo and token:
        body = _build_issue_body(idea, worker_messages, conclusion_text, personal_scores)
        issue_url = create_github_issue(
            repo=repo,
            token=token,
            title=f"[アイデア採用] {idea['title']}",
            body=body,
        )

    update_meeting_conclusion(conn, session_id, conclusion, issue_url or None)
    update_personal_scores(
        conn,
        session_id,
        japan_demand=personal_scores["japan_demand"],
        solo_customer=personal_scores["solo_customer"],
        revenue_6mo=personal_scores["revenue_6mo"],
        background_fit=personal_scores["background_fit"],
    )
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
