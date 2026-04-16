"""Claude API agent calls for the meeting system.

Each agent role has a persona defined in .claude/agents/{role}.md.
The persona file is loaded as the system prompt for every API call.
"""

from pathlib import Path

import anthropic

# Path to agent persona definition files
AGENTS_DIR = Path(__file__).parent.parent / ".claude" / "agents"

MODEL = "claude-sonnet-4-6"

AGENT_ROLES: list[str] = ["planning", "sales", "marketing", "dev", "ops"]
CEO_ROLE: str = "ceo"

_client = anthropic.Anthropic()


def load_agent_persona(role: str) -> str:
    """Read and return the persona markdown for *role*.

    Raises FileNotFoundError if the persona file does not exist.
    """
    persona_path = AGENTS_DIR / f"{role}.md"
    if not persona_path.exists():
        raise FileNotFoundError(f"Persona file not found: {persona_path}")
    return persona_path.read_text(encoding="utf-8")


def _build_user_message(idea: dict, history: list[dict]) -> str:
    """Build the user-turn content for the current agent call."""
    if not history:
        return (
            f"議題のアイデアを以下に示します。評価してください。\n\n"
            f"## アイデア名\n{idea.get('title', '')}\n\n"
            f"## 概要\n{idea.get('description', '')}\n\n"
            f"## ターゲット市場\n{idea.get('target_market', '')}\n\n"
            f"## なぜ今か\n{idea.get('why_now', '')}\n\n"
            f"## 収益モデル\n{idea.get('revenue_model', '')}\n\n"
            f"## 難易度\n{idea.get('difficulty', '')}\n\n"
            f"## 総合スコア\n{idea.get('eval_total', '')}/10\n"
        )
    prior = "\n".join(f"[{m['role']}] {m['content']}" for m in history)
    return f"これまでの議論:\n{prior}\n\nあなたの担当の観点から意見をお願いします。"


def call_agent(role: str, idea: dict, history: list[dict]) -> str:
    """Call Claude with the given agent's persona and return the response text.

    Returns an empty string on any API error so the meeting can continue.
    """
    try:
        system_prompt = load_agent_persona(role)
        user_content = _build_user_message(idea, history)

        # Build messages list from history, then append the new user turn
        messages: list[dict] = []
        for entry in history:
            msg_role = "assistant" if entry["role"] == "assistant" else "user"
            messages.append({"role": msg_role, "content": entry["content"]})

        if not messages or messages[-1]["role"] != "user":
            messages.append({"role": "user", "content": user_content})
        else:
            messages[-1]["content"] += f"\n\n{user_content}"

        response = _client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=system_prompt,
            messages=messages,
        )
        return response.content[0].text
    except Exception:
        return ""
