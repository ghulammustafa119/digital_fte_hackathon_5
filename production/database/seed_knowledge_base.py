"""Seed the knowledge base with product documentation from context/product-docs.md."""

import asyncio
import os
import asyncpg


DOCS_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "context", "product-docs.md")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://fte_user:fte_password@localhost:5432/fte_db")


def parse_product_docs(filepath: str) -> list[dict]:
    """Parse product-docs.md into knowledge base entries by section."""
    with open(filepath, "r") as f:
        content = f.read()

    entries = []
    current_category = "general"

    # Split by ## headers (main sections)
    sections = content.split("\n## ")
    for section in sections:
        if not section.strip():
            continue

        lines = section.strip().split("\n")
        title = lines[0].replace("#", "").strip()
        body = "\n".join(lines[1:]).strip()

        if not title or not body:
            continue

        # Determine category from title
        title_lower = title.lower()
        if any(w in title_lower for w in ["getting started", "creating", "account"]):
            current_category = "getting_started"
        elif any(w in title_lower for w in ["task", "board", "view", "subtask", "depend"]):
            current_category = "task_management"
        elif any(w in title_lower for w in ["collaborat", "comment", "notif", "real-time"]):
            current_category = "collaboration"
        elif any(w in title_lower for w in ["time", "tracking", "timer"]):
            current_category = "time_tracking"
        elif any(w in title_lower for w in ["integrat", "slack", "github", "google", "zapier"]):
            current_category = "integrations"
        elif any(w in title_lower for w in ["automat", "rule", "trigger"]):
            current_category = "automations"
        elif any(w in title_lower for w in ["report", "dashboard", "analytics"]):
            current_category = "reports"
        elif any(w in title_lower for w in ["billing", "plan", "cancel", "export"]):
            current_category = "billing"
        elif any(w in title_lower for w in ["security", "password", "2fa", "sso"]):
            current_category = "security"
        elif any(w in title_lower for w in ["api", "webhook", "endpoint"]):
            current_category = "api"
        elif any(w in title_lower for w in ["troubleshoot", "common", "issue", "faq"]):
            current_category = "troubleshooting"

        # Split large sections into sub-sections by ### headers
        sub_sections = body.split("\n### ")
        if len(sub_sections) > 1:
            for sub in sub_sections:
                sub_lines = sub.strip().split("\n")
                sub_title = sub_lines[0].replace("#", "").strip()
                sub_body = "\n".join(sub_lines[1:]).strip()
                if sub_title and sub_body:
                    entries.append({
                        "title": f"{title} - {sub_title}",
                        "content": sub_body,
                        "category": current_category,
                    })
        else:
            entries.append({
                "title": title,
                "content": body,
                "category": current_category,
            })

    return entries


async def seed_knowledge_base():
    """Insert parsed documentation into the knowledge_base table."""
    if not os.path.exists(DOCS_PATH):
        print(f"ERROR: Product docs not found at {DOCS_PATH}")
        return

    entries = parse_product_docs(DOCS_PATH)
    print(f"Parsed {len(entries)} knowledge base entries from product docs")

    conn = await asyncpg.connect(DATABASE_URL)

    try:
        # Clear existing entries
        deleted = await conn.execute("DELETE FROM knowledge_base WHERE category IS NOT NULL")
        print(f"Cleared existing entries: {deleted}")

        # Insert new entries
        inserted = 0
        for entry in entries:
            await conn.execute(
                """INSERT INTO knowledge_base (title, content, category)
                   VALUES ($1, $2, $3)""",
                entry["title"],
                entry["content"],
                entry["category"],
            )
            inserted += 1

        print(f"Inserted {inserted} knowledge base entries")

        # Show category distribution
        rows = await conn.fetch(
            "SELECT category, COUNT(*) as count FROM knowledge_base GROUP BY category ORDER BY count DESC"
        )
        print("\nCategory distribution:")
        for row in rows:
            print(f"  {row['category']}: {row['count']} entries")

    finally:
        await conn.close()


async def seed_channel_configs():
    """Ensure channel configurations exist."""
    conn = await asyncpg.connect(DATABASE_URL)

    try:
        # Check if already seeded
        count = await conn.fetchval("SELECT COUNT(*) FROM channel_configs")
        if count >= 3:
            print(f"Channel configs already seeded ({count} entries)")
            return

        print("Seeding channel configurations...")
        configs = [
            ("email", True, '{"provider": "gmail", "poll_interval_seconds": 30}',
             "Hi {{customer_name}},\n\nThank you for reaching out to FlowBoard Support.\n\n{{response}}\n\nBest regards,\nFlowBoard Support Team",
             2000),
            ("whatsapp", True, '{"provider": "twilio"}',
             "{{response}}\n\nReply for more help or type 'human' for live support.",
             1600),
            ("web_form", True, '{"version": "1.0"}',
             "{{response}}\n\n---\nNeed more help? Reply or visit our support portal.",
             1000),
        ]

        for channel, enabled, config, template, max_len in configs:
            await conn.execute(
                """INSERT INTO channel_configs (channel, enabled, config, response_template, max_response_length)
                   VALUES ($1, $2, $3::jsonb, $4, $5)
                   ON CONFLICT (channel) DO NOTHING""",
                channel, enabled, config, template, max_len,
            )

        print("Channel configs seeded successfully")

    finally:
        await conn.close()


async def main():
    print("=" * 60)
    print("SEEDING DATABASE")
    print("=" * 60)
    print(f"Database: {DATABASE_URL}")
    print(f"Docs path: {DOCS_PATH}")
    print()

    await seed_knowledge_base()
    print()
    await seed_channel_configs()

    print()
    print("Seeding complete!")


if __name__ == "__main__":
    asyncio.run(main())
