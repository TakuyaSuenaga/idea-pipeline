"""Main pipeline entry point. Called by GitHub Actions."""

import sys

from pipeline.db import (
    DB_PATH,
    cleanup_old_research,
    fetch_all_ideas,
    fetch_recent_research,
    init_db,
    insert_idea,
    insert_research,
)
from pipeline.export import export_ideas, export_research
from pipeline.ideation import generate_ideas
from pipeline.research import run_research


def main() -> None:
    print("=== Idea Pipeline Run ===")

    conn = init_db(DB_PATH)

    print("Fetching market research...")
    research_items = run_research()
    print(f"  Found {len(research_items)} items")

    for item in research_items:
        insert_research(
            conn,
            source=item["source"],
            title=item["title"],
            url=item.get("url"),
            content=item.get("content"),
            score=item.get("score"),
            category=item.get("category"),
        )

    deleted = cleanup_old_research(conn, days=7)
    print(f"  Cleaned up {deleted} old research items")

    recent_research = fetch_recent_research(conn, days=7)
    if not recent_research:
        print("  No recent research — skipping ideation")
        conn.close()
        sys.exit(0)

    print("Generating startup ideas...")
    ideas = generate_ideas(recent_research)
    print(f"  Generated {len(ideas)} ideas")

    if not ideas:
        print("  No ideas generated — exiting without commit")
        conn.close()
        sys.exit(0)

    for idea in ideas:
        insert_idea(
            conn,
            title=idea.get("title", ""),
            description=idea.get("description", ""),
            target_market=idea.get("target_market"),
            why_now=idea.get("why_now"),
            revenue_model=idea.get("revenue_model"),
            difficulty=idea.get("difficulty"),
            category=idea.get("category"),
            research_ids=[r["id"] for r in recent_research[:20]],
        )

    print("Exporting to docs/data/ ...")
    all_ideas = fetch_all_ideas(conn)
    export_ideas(all_ideas)
    export_research(recent_research)

    conn.close()
    print("=== Pipeline complete ===")


if __name__ == "__main__":
    main()
