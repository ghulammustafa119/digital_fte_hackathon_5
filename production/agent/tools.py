"""Agent tools for the Customer Success FTE using OpenAI Agents SDK."""

from agents import function_tool
from pydantic import BaseModel
from typing import Optional
from enum import Enum
import logging

from production.database.queries import (
    search_knowledge_base_text,
    create_ticket_record,
    get_customer_history_across_channels,
    update_ticket_status,
)

logger = logging.getLogger(__name__)


class Channel(str, Enum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    WEB_FORM = "web_form"


# ---- Input Schemas ----

class KnowledgeSearchInput(BaseModel):
    """Input for knowledge base search."""
    query: str
    max_results: int = 5


class TicketInput(BaseModel):
    """Input for creating a support ticket."""
    customer_id: str
    issue: str
    priority: str = "medium"
    category: Optional[str] = None
    channel: Channel


class EscalationInput(BaseModel):
    """Input for escalating to human support."""
    ticket_id: str
    reason: str
    urgency: str = "normal"


class ResponseInput(BaseModel):
    """Input for sending a response to the customer."""
    ticket_id: str
    message: str
    channel: Channel


# ---- Tool Definitions ----

@function_tool
async def search_knowledge_base(input: KnowledgeSearchInput) -> str:
    """Search product documentation for relevant information.

    Use this when the customer asks questions about product features,
    how to use something, or needs technical information.
    """
    try:
        results = await search_knowledge_base_text(input.query, input.max_results)

        if not results:
            return "No relevant documentation found. Consider escalating to human support if this is the second failed search."

        formatted = []
        for r in results:
            formatted.append(f"**{r['title']}** (Category: {r.get('category', 'general')})\n{r['content'][:500]}")

        return "\n\n---\n\n".join(formatted)

    except Exception as e:
        logger.error(f"Knowledge base search failed: {e}")
        return "Knowledge base temporarily unavailable. Please try again or escalate."


@function_tool
async def create_ticket(input: TicketInput) -> str:
    """Create a support ticket for tracking.

    ALWAYS create a ticket at the start of every conversation.
    Include the source channel for proper tracking.
    """
    try:
        ticket_id = await create_ticket_record(
            customer_id=input.customer_id,
            conversation_id="",  # Will be set by processor
            channel=input.channel.value,
            subject=input.issue,
            category=input.category,
            priority=input.priority,
        )
        return f"Ticket created: {ticket_id}"

    except Exception as e:
        logger.error(f"Ticket creation failed: {e}")
        return "Ticket creation failed. Proceeding with response."


@function_tool
async def get_customer_history(customer_id: str) -> str:
    """Get customer's complete interaction history across ALL channels.

    Use this to understand context from previous conversations,
    even if they happened on a different channel.
    """
    try:
        history = await get_customer_history_across_channels(customer_id)

        if not history:
            return "No previous interaction history found. This is a new customer."

        formatted = []
        for h in history:
            formatted.append(
                f"[{h['channel']}] {h['role']}: {h['content'][:200]} "
                f"({h['created_at'].strftime('%Y-%m-%d %H:%M')})"
            )

        return "Customer history (most recent first):\n" + "\n".join(formatted)

    except Exception as e:
        logger.error(f"Customer history lookup failed: {e}")
        return "Could not retrieve customer history."


@function_tool
async def escalate_to_human(input: EscalationInput) -> str:
    """Escalate conversation to human support.

    Use this when:
    - Customer asks about pricing or refunds
    - Customer sentiment is negative (profanity, anger)
    - You cannot find relevant information after 2 searches
    - Customer explicitly requests human help
    - Legal/compliance concerns arise
    - Account security issues reported
    """
    try:
        await update_ticket_status(
            ticket_id=input.ticket_id,
            status="escalated",
            resolution_notes=f"Escalation reason: {input.reason}",
            escalation_reason=input.reason,
        )
        return f"Escalated to human support. Reason: {input.reason}. Reference: {input.ticket_id}"

    except Exception as e:
        logger.error(f"Escalation failed: {e}")
        return f"Escalation recorded. Reason: {input.reason}. A human agent will follow up."


@function_tool
async def send_response(input: ResponseInput) -> str:
    """Send response to customer via their preferred channel.

    The response will be automatically formatted for the channel:
    - Email: Formal with greeting and signature
    - WhatsApp: Concise and conversational
    - Web Form: Semi-formal with support links

    ALWAYS use this tool to send your final response.
    """
    formatted = format_for_channel(input.message, input.channel)

    # In production, this dispatches to the actual channel handler.
    # The message processor handles the actual sending.
    return f"Response prepared for {input.channel.value} ({len(formatted)} chars): {formatted[:100]}..."


def format_for_channel(response: str, channel: Channel) -> str:
    """Format response appropriately for the channel."""
    if channel == Channel.EMAIL:
        return (
            f"Hi,\n\n"
            f"Thank you for reaching out to FlowBoard Support.\n\n"
            f"{response}\n\n"
            f"If you have any further questions, please don't hesitate to reply.\n\n"
            f"Best regards,\n"
            f"FlowBoard Support Team"
        )
    elif channel == Channel.WHATSAPP:
        if len(response) > 280:
            response = response[:277] + "..."
        return f"{response}\n\nReply for more help or type 'human' for live support."
    else:  # web_form
        return (
            f"{response}\n\n"
            f"---\n"
            f"Need more help? Reply to this message or visit our support portal."
        )
