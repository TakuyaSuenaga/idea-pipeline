"""Startup idea generation using the Claude API."""

import json
import re
from pathlib import Path

import anthropic

_SKILL_MD_PATH = (
    Path(__file__).parent.parent / ".agents" / "skills" / "startup-ideation" / "SKILL.md"
)

_SYSTEM_PROMPT_TEMPLATE = """\
You are a startup idea generator for a Japanese solo entrepreneur who recently founded \
a sole proprietorship. You specialize in IT/SaaS and SEO business ideas.

## Your Constraints
- Ideas must be achievable by a single developer without employees
- Focus on recurring revenue (subscription/SaaS) or content/SEO monetization
- Avoid ideas requiring large capital, physical goods, or large teams
- Target: global market accessible from Japan OR Japan-specific digital market

## Ideation Framework
{skill_md_content}

## Output Format
Respond with a JSON array (no markdown code fences, no surrounding text) of 3-5 startup ideas.
Each idea must have exactly these keys:
- title: string (concise product name, in Japanese)
- description: string (2-3 sentences on what it does and who it is for, in Japanese)
- target_market: string (specific customer segment, in Japanese)
- why_now: string (what recent change makes this viable now, in Japanese)
- revenue_model: string (how money is made, in Japanese)
- difficulty: "low" | "medium" | "high"
- category: "saas" | "seo"
- evaluation: object with exactly these keys:
  - why_now_score: integer 1-10 (strength of the Why Now angle)
  - differentiation_score: integer 1-10 (how unique / off the beaten path)
  - feasibility_score: integer 1-10 (how feasible for a solo developer)
  - market_size_score: integer 1-10 (market size potential)
  - comment: string (brief evaluation summary in Japanese, 1-2 sentences)

**IMPORTANT: Write all text values (title, description, target_market, why_now, revenue_model, evaluation.comment) in Japanese. Only the enum values (difficulty, category) and integer scores remain in English/numeric.**

Apply the Why Now test to every idea. Flag and avoid tarpit ideas. Score honestly — most ideas should score 5-8; reserve 9-10 for exceptional ideas.
"""


def _load_skill_md() -> str:
    try:
        return _SKILL_MD_PATH.read_text(encoding="utf-8")
    except OSError:
        return "(skill content unavailable)"


def _parse_ideas_json(text: str) -> list[dict]:
    """Extract and parse a JSON array from Claude's response text."""
    cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```\s*$", "", cleaned.strip(), flags=re.MULTILINE)
    cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
        if isinstance(data, list):
            return [idea for idea in (_validate_idea(i) for i in data) if idea is not None]
        return []
    except json.JSONDecodeError:
        pass

    # Fallback: find a JSON array anywhere in the text
    match = re.search(r"\[[\s\S]*?\]", text)
    if match:
        try:
            data = json.loads(match.group())
            if isinstance(data, list):
                return [idea for idea in (_validate_idea(i) for i in data) if idea is not None]
        except json.JSONDecodeError:
            pass

    return []


def _clamp_score(value) -> int | None:
    """Return value clamped to 1–10 if castable to int, else None."""
    try:
        v = int(value)
        return max(1, min(10, v))
    except (TypeError, ValueError):
        return None


def _validate_idea(idea: dict) -> dict | None:
    """Validate and normalise a single idea dict. Returns None if invalid."""
    if not isinstance(idea, dict):
        return None
    if not all(k in idea for k in ("title", "description", "category")):
        return None
    if idea.get("difficulty") not in ("low", "medium", "high"):
        idea["difficulty"] = "medium"
    if idea.get("category") not in ("saas", "seo"):
        idea["category"] = "saas"

    # Flatten nested evaluation object into top-level eval_* keys
    eval_data = idea.pop("evaluation", None) or {}
    idea["eval_why_now"] = _clamp_score(eval_data.get("why_now_score"))
    idea["eval_differentiation"] = _clamp_score(eval_data.get("differentiation_score"))
    idea["eval_feasibility"] = _clamp_score(eval_data.get("feasibility_score"))
    idea["eval_market_size"] = _clamp_score(eval_data.get("market_size_score"))
    comment = eval_data.get("comment")
    idea["eval_comment"] = comment if isinstance(comment, str) else None

    return idea


def generate_ideas(research_items: list[dict]) -> list[dict]:
    """Call Claude to generate startup ideas based on recent research."""
    if not research_items:
        return []

    skill_content = _load_skill_md()
    system_text = _SYSTEM_PROMPT_TEMPLATE.format(skill_md_content=skill_content)

    research_summary = "\n\n".join(
        f"[{item.get('source', 'unknown')}] {item.get('title', '')}\n"
        f"{(item.get('content') or '')[:300]}"
        for item in research_items[:20]
    )

    user_message = (
        "Based on this market research from the last 7 days, generate 3-5 startup ideas:\n\n"
        f"{research_summary}\n\n"
        "Remember: Go off the beaten path. What is newly possible? Apply the Why Now test."
    )

    client = anthropic.Anthropic()
    try:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=4096,
            system=[
                {
                    "type": "text",
                    "text": system_text,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": user_message}],
        )
        text = next(
            (block.text for block in response.content if block.type == "text"), ""
        )
        return _parse_ideas_json(text)

    except anthropic.APIStatusError as exc:
        print(f"Claude API error {exc.status_code}: {exc.message}")
        return []
    except anthropic.APIConnectionError:
        print("Claude API connection error")
        return []
