"""MCP Server - Customer Success FTE tools exposed via Model Context Protocol."""

from mcp.server import Server
from mcp.types import Tool, TextContent
from enum import Enum
from typing import Optional
import json

class Channel(str, Enum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    WEB_FORM = "web_form"


# In-memory storage for prototype
conversations = {}
tickets = {}
knowledge_base = []
customers = {}

server = Server("customer-success-fte")


@server.tool("search_knowledge_base")
async def search_kb(query: str, max_results: int = 5) -> str:
    """Search product documentation for relevant information.

    Use this when the customer asks questions about product features,
    how to use something, or needs technical information.
    """
    query_lower = query.lower()
    results = []
    for entry in knowledge_base:
        if query_lower in entry["title"].lower() or query_lower in entry["content"].lower():
            results.append(entry)
        if len(results) >= max_results:
            break

    if not results:
        # Try partial word matching
        query_words = query_lower.split()
        for entry in knowledge_base:
            text = (entry["title"] + " " + entry["content"]).lower()
            if any(word in text for word in query_words):
                results.append(entry)
            if len(results) >= max_results:
                break

    if not results:
        return "No relevant documentation found. Consider escalating to human support."

    formatted = []
    for r in results:
        formatted.append(f"**{r['title']}** (Category: {r.get('category', 'general')})\n{r['content'][:500]}")

    return "\n\n---\n\n".join(formatted)


@server.tool("create_ticket")
async def create_ticket(
    customer_id: str,
    issue: str,
    priority: str = "medium",
    channel: str = "web_form",
    category: Optional[str] = None,
) -> str:
    """Create a support ticket in the system with channel tracking.

    ALWAYS create a ticket at the start of every conversation.
    Include the source channel for proper tracking.
    """
    import uuid

    ticket_id = str(uuid.uuid4())[:8]
    tickets[ticket_id] = {
        "id": ticket_id,
        "customer_id": customer_id,
        "issue": issue,
        "priority": priority,
        "channel": channel,
        "category": category,
        "status": "open",
    }
    return f"Ticket created: {ticket_id}"


@server.tool("get_customer_history")
async def get_customer_history(customer_id: str) -> str:
    """Get customer's interaction history across ALL channels.

    Use this to understand context from previous conversations,
    even if they happened on a different channel.
    """
    if customer_id not in customers:
        return "No previous interaction history found. This is a new customer."

    customer = customers[customer_id]
    history = customer.get("history", [])

    if not history:
        return "No previous interaction history found."

    formatted = []
    for h in history[-10:]:
        formatted.append(f"[{h.get('channel', 'unknown')}] {h.get('role', 'unknown')}: {h.get('content', '')[:200]}")

    return "Customer history (most recent):\n" + "\n".join(formatted)


@server.tool("escalate_to_human")
async def escalate_to_human(ticket_id: str, reason: str, urgency: str = "normal") -> str:
    """Escalate conversation to human support.

    Use this when:
    - Customer asks about pricing or refunds
    - Customer sentiment is negative (profanity, anger)
    - You cannot find relevant information after 2 searches
    - Customer explicitly requests human help
    - Legal/compliance concerns arise
    - Account security issues reported
    """
    if ticket_id in tickets:
        tickets[ticket_id]["status"] = "escalated"
        tickets[ticket_id]["escalation_reason"] = reason

    return f"Escalated to human support. Reason: {reason}. Reference: {ticket_id}. A human agent will follow up shortly."


@server.tool("send_response")
async def send_response(ticket_id: str, message: str, channel: str = "web_form") -> str:
    """Send response to customer via the appropriate channel.

    The response will be automatically formatted for the channel:
    - Email: Formal with greeting and signature
    - WhatsApp: Concise and conversational
    - Web Form: Semi-formal with support links

    ALWAYS use this tool to send your final response.
    """
    if channel == "email":
        formatted = (
            f"Hi,\n\nThank you for reaching out to FlowBoard Support.\n\n"
            f"{message}\n\n"
            f"If you have any further questions, please don't hesitate to reply.\n\n"
            f"Best regards,\nFlowBoard Support Team"
        )
    elif channel == "whatsapp":
        if len(message) > 280:
            message = message[:277] + "..."
        formatted = f"{message}\n\nReply for more help or type 'human' for live support."
    else:
        formatted = f"{message}\n\n---\nNeed more help? Reply to this message or visit our support portal."

    return f"Response sent via {channel}: {formatted[:100]}..."


@server.tool("get_ticket_status")
async def get_ticket_status(ticket_id: str) -> str:
    """Get the current status of a support ticket.

    Use this to check if a ticket has been resolved, escalated, or is still open.
    """
    if ticket_id not in tickets:
        return f"Ticket {ticket_id} not found."

    ticket = tickets[ticket_id]
    return json.dumps(ticket, indent=2)


@server.tool("update_customer_sentiment")
async def update_customer_sentiment(customer_id: str, sentiment_score: float, notes: str = "") -> str:
    """Track customer sentiment during the conversation.

    Call this after analyzing each customer message.
    Score: 0.0 (very negative) to 1.0 (very positive)
    If score < 0.3, consider escalating.
    """
    if customer_id not in customers:
        customers[customer_id] = {"id": customer_id, "history": []}

    customers[customer_id]["sentiment"] = sentiment_score
    customers[customer_id]["sentiment_notes"] = notes

    if sentiment_score < 0.3:
        return f"Sentiment recorded: {sentiment_score} (LOW - consider escalation). Notes: {notes}"

    return f"Sentiment recorded: {sentiment_score}. Notes: {notes}"


def load_knowledge_base_from_file(filepath: str):
    """Load product documentation into the knowledge base."""
    import os
    if not os.path.exists(filepath):
        return

    with open(filepath, "r") as f:
        content = f.read()

    # Split by ## headers
    sections = content.split("\n## ")
    for section in sections:
        if not section.strip():
            continue
        lines = section.strip().split("\n")
        title = lines[0].replace("#", "").strip()
        body = "\n".join(lines[1:]).strip()
        if title and body:
            knowledge_base.append({
                "title": title,
                "content": body,
                "category": "product_docs",
            })


# Load knowledge base on startup
import os
docs_path = os.path.join(os.path.dirname(__file__), "..", "..", "context", "product-docs.md")
load_knowledge_base_from_file(os.path.abspath(docs_path))


if __name__ == "__main__":
    import asyncio
    print(f"MCP Server 'customer-success-fte' starting with {len(knowledge_base)} KB entries...")
    print(f"Tools available: search_knowledge_base, create_ticket, get_customer_history, "
          f"escalate_to_human, send_response, get_ticket_status, update_customer_sentiment")
    server.run()
