"""Database access functions for the Customer Success FTE."""

import os
import asyncpg
from typing import Optional

_pool: Optional[asyncpg.Pool] = None


async def get_db_pool() -> asyncpg.Pool:
    """Get or create the database connection pool."""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            dsn=os.getenv("DATABASE_URL", "postgresql://fte_user:fte_password@localhost:5432/fte_db"),
            min_size=2,
            max_size=10,
        )
    return _pool


async def close_db_pool():
    """Close the database connection pool."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


# ---- Customer Queries ----

async def find_customer_by_email(email: str) -> Optional[dict]:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM customers WHERE email = $1", email)
        return dict(row) if row else None


async def find_customer_by_phone(phone: str) -> Optional[dict]:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """SELECT c.* FROM customers c
               JOIN customer_identifiers ci ON ci.customer_id = c.id
               WHERE ci.identifier_type = 'whatsapp' AND ci.identifier_value = $1""",
            phone,
        )
        return dict(row) if row else None


async def create_customer(email: str = None, phone: str = None, name: str = "") -> str:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        customer_id = await conn.fetchval(
            "INSERT INTO customers (email, phone, name) VALUES ($1, $2, $3) RETURNING id",
            email, phone, name,
        )
        if phone:
            await conn.execute(
                """INSERT INTO customer_identifiers (customer_id, identifier_type, identifier_value)
                   VALUES ($1, 'whatsapp', $2) ON CONFLICT DO NOTHING""",
                customer_id, phone,
            )
        return str(customer_id)


# ---- Conversation Queries ----

async def get_active_conversation(customer_id: str) -> Optional[str]:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """SELECT id FROM conversations
               WHERE customer_id = $1 AND status = 'active'
                 AND started_at > NOW() - INTERVAL '24 hours'
               ORDER BY started_at DESC LIMIT 1""",
            customer_id,
        )
        return str(row["id"]) if row else None


async def create_conversation(customer_id: str, channel: str) -> str:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        conv_id = await conn.fetchval(
            """INSERT INTO conversations (customer_id, initial_channel, status)
               VALUES ($1, $2, 'active') RETURNING id""",
            customer_id, channel,
        )
        return str(conv_id)


# ---- Message Queries ----

async def store_message(
    conversation_id: str,
    channel: str,
    direction: str,
    role: str,
    content: str,
    channel_message_id: str = None,
    latency_ms: int = None,
    tool_calls: list = None,
) -> str:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        import json
        msg_id = await conn.fetchval(
            """INSERT INTO messages (conversation_id, channel, direction, role, content,
                                    channel_message_id, latency_ms, tool_calls)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb) RETURNING id""",
            conversation_id, channel, direction, role, content,
            channel_message_id, latency_ms,
            json.dumps(tool_calls or []),
        )
        return str(msg_id)


async def get_conversation_messages(conversation_id: str, limit: int = 20) -> list:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT role, content, channel, created_at
               FROM messages WHERE conversation_id = $1
               ORDER BY created_at ASC LIMIT $2""",
            conversation_id, limit,
        )
        return [dict(r) for r in rows]


# ---- Ticket Queries ----

async def create_ticket_record(
    customer_id: str,
    conversation_id: str,
    channel: str,
    subject: str = None,
    category: str = None,
    priority: str = "medium",
) -> str:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        ticket_id = await conn.fetchval(
            """INSERT INTO tickets (customer_id, conversation_id, source_channel, subject, category, priority)
               VALUES ($1, $2, $3, $4, $5, $6) RETURNING id""",
            customer_id, conversation_id, channel, subject, category, priority,
        )
        return str(ticket_id)


async def update_ticket_status(ticket_id: str, status: str, resolution_notes: str = None, escalation_reason: str = None):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """UPDATE tickets SET status = $2, resolution_notes = $3, escalation_reason = $4,
                   updated_at = NOW(),
                   resolved_at = CASE WHEN $2 IN ('resolved', 'closed') THEN NOW() ELSE resolved_at END
               WHERE id = $1""",
            ticket_id, status, resolution_notes, escalation_reason,
        )


async def get_ticket_by_id(ticket_id: str) -> Optional[dict]:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM tickets WHERE id = $1", ticket_id)
        return dict(row) if row else None


# ---- Customer History ----

async def get_customer_history_across_channels(customer_id: str, limit: int = 20) -> list:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT c.initial_channel, c.started_at, c.status as conv_status,
                      m.content, m.role, m.channel, m.created_at
               FROM conversations c
               JOIN messages m ON m.conversation_id = c.id
               WHERE c.customer_id = $1
               ORDER BY m.created_at DESC LIMIT $2""",
            customer_id, limit,
        )
        return [dict(r) for r in rows]


# ---- Knowledge Base ----

async def search_knowledge_base_text(query: str, max_results: int = 5) -> list:
    """Simple text search fallback (used when embeddings not available)."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT title, content, category
               FROM knowledge_base
               WHERE content ILIKE '%' || $1 || '%' OR title ILIKE '%' || $1 || '%'
               LIMIT $2""",
            query, max_results,
        )
        return [dict(r) for r in rows]


async def search_knowledge_base_vector(embedding: list, max_results: int = 5) -> list:
    """Vector similarity search using pgvector."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT title, content, category,
                      1 - (embedding <=> $1::vector) as similarity
               FROM knowledge_base
               WHERE embedding IS NOT NULL
               ORDER BY embedding <=> $1::vector
               LIMIT $2""",
            str(embedding), max_results,
        )
        return [dict(r) for r in rows]


# ---- Metrics ----

async def record_metric(metric_name: str, metric_value: float, channel: str = None, dimensions: dict = None):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        import json
        await conn.execute(
            """INSERT INTO agent_metrics (metric_name, metric_value, channel, dimensions)
               VALUES ($1, $2, $3, $4::jsonb)""",
            metric_name, metric_value, channel, json.dumps(dimensions or {}),
        )


async def get_channel_metrics() -> list:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT initial_channel as channel,
                      COUNT(*) as total_conversations,
                      AVG(sentiment_score) as avg_sentiment,
                      COUNT(*) FILTER (WHERE status = 'escalated') as escalations
               FROM conversations
               WHERE started_at > NOW() - INTERVAL '24 hours'
               GROUP BY initial_channel""",
        )
        return [dict(r) for r in rows]


# ---- Delivery Status ----

async def update_delivery_status(channel_message_id: str, status: str):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE messages SET delivery_status = $2 WHERE channel_message_id = $1",
            channel_message_id, status,
        )
