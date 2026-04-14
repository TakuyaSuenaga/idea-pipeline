"""Export DB data to JSON files for GitHub Pages."""

import json
from datetime import datetime, timezone
from pathlib import Path

DOCS_DATA_DIR = Path(__file__).parent.parent / "docs" / "data"


def export_ideas(ideas: list[dict]) -> None:
    """Write all ideas to docs/data/ideas.json."""
    DOCS_DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "count": len(ideas),
        "ideas": ideas,
    }
    (DOCS_DATA_DIR / "ideas.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def export_research(research: list[dict]) -> None:
    """Write recent research to docs/data/research.json."""
    DOCS_DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "count": len(research),
        "items": research,
    }
    (DOCS_DATA_DIR / "research.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
