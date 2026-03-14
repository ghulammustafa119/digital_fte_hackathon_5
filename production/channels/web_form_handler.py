"""Web support form handler - FastAPI router."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
from typing import Optional
import uuid
import logging

from production.database.queries import create_ticket_record, get_ticket_by_id, get_conversation_messages

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/support", tags=["support-form"])


class SupportFormSubmission(BaseModel):
    """Support form submission model with validation."""
    name: str
    email: EmailStr
    subject: str
    category: str
    message: str
    priority: Optional[str] = "medium"

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError("Name must be at least 2 characters")
        return v.strip()

    @field_validator("message")
    @classmethod
    def message_must_have_content(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError("Message must be at least 10 characters")
        return v.strip()

    @field_validator("category")
    @classmethod
    def category_must_be_valid(cls, v):
        valid_categories = ["general", "technical", "billing", "feedback", "bug_report"]
        if v not in valid_categories:
            raise ValueError(f"Category must be one of: {valid_categories}")
        return v

    @field_validator("subject")
    @classmethod
    def subject_must_have_content(cls, v):
        if not v or len(v.strip()) < 5:
            raise ValueError("Subject must be at least 5 characters")
        return v.strip()


class SupportFormResponse(BaseModel):
    """Response model for form submission."""
    ticket_id: str
    message: str
    estimated_response_time: str


@router.post("/submit", response_model=SupportFormResponse)
async def submit_support_form(submission: SupportFormSubmission):
    """Handle support form submission.

    1. Validates the submission
    2. Creates a normalized message for agent processing
    3. Publishes to Kafka for agent processing
    4. Returns confirmation to user
    """
    ticket_id = str(uuid.uuid4())

    message_data = {
        "channel": "web_form",
        "channel_message_id": ticket_id,
        "customer_email": submission.email,
        "customer_name": submission.name,
        "subject": submission.subject,
        "content": submission.message,
        "category": submission.category,
        "priority": submission.priority,
        "received_at": datetime.utcnow().isoformat(),
        "metadata": {"form_version": "1.0"},
    }

    # Publish to Kafka (imported at runtime to avoid circular imports)
    try:
        from production.api.main import kafka_producer
        from production.kafka_client import TOPICS

        await kafka_producer.publish(TOPICS["tickets_incoming"], message_data)
    except Exception as e:
        logger.error(f"Failed to publish to Kafka: {e}")

    return SupportFormResponse(
        ticket_id=ticket_id,
        message="Thank you for contacting us! Our AI assistant will respond shortly.",
        estimated_response_time="Usually within 5 minutes",
    )


@router.get("/ticket/{ticket_id}")
async def get_ticket_status(ticket_id: str):
    """Get status and conversation history for a ticket."""
    ticket = await get_ticket_by_id(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    messages = []
    if ticket.get("conversation_id"):
        messages = await get_conversation_messages(str(ticket["conversation_id"]))

    return {
        "ticket_id": ticket_id,
        "status": ticket["status"],
        "category": ticket.get("category"),
        "priority": ticket.get("priority"),
        "messages": messages,
        "created_at": ticket["created_at"].isoformat() if ticket.get("created_at") else None,
        "last_updated": ticket["updated_at"].isoformat() if ticket.get("updated_at") else None,
    }
