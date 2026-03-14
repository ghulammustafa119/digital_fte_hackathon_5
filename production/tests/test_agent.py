"""Tests for Customer Success Agent behavior and tool execution."""

import pytest
from unittest.mock import AsyncMock, patch

from production.agent.tools import (
    Channel,
    create_ticket,
    escalate_to_human,
    send_response,
    format_for_channel,
    TicketInput,
    EscalationInput,
    ResponseInput,
)


class TestChannelResponseFormatting:
    """Test response formatting for different channels."""

    def test_email_has_greeting_and_signature(self):
        response = "This is a test response"
        formatted = format_for_channel(response, Channel.EMAIL)
        assert "hi" in formatted.lower()
        assert "regards" in formatted.lower()
        assert response in formatted

    def test_whatsapp_is_concise(self):
        response = "This is a short response"
        formatted = format_for_channel(response, Channel.WHATSAPP)
        assert len(formatted) < 600
        assert "human" in formatted.lower()

    def test_whatsapp_truncates_long_messages(self):
        long_response = "This is a very long response. " * 50
        formatted = format_for_channel(long_response, Channel.WHATSAPP)
        assert "..." in formatted

    def test_web_form_includes_support_link(self):
        response = "Here is your answer"
        formatted = format_for_channel(response, Channel.WEB_FORM)
        assert "support" in formatted.lower()


class TestToolExecution:
    """Test agent tools with mocked database."""

    @pytest.mark.asyncio
    async def test_create_ticket_success(self):
        with patch("production.agent.tools.create_ticket_record", new_callable=AsyncMock) as mock:
            mock.return_value = "ticket-123"
            result = await create_ticket(TicketInput(
                customer_id="cust-1", issue="Test issue", channel=Channel.EMAIL
            ))
            assert "ticket-123" in result

    @pytest.mark.asyncio
    async def test_escalation_updates_ticket(self):
        with patch("production.agent.tools.update_ticket_status", new_callable=AsyncMock) as mock:
            mock.return_value = None
            result = await escalate_to_human(EscalationInput(
                ticket_id="ticket-1", reason="pricing_inquiry"
            ))
            assert "escalated" in result.lower()
            mock.assert_called_once()
            assert mock.call_args[1]["status"] == "escalated"

    @pytest.mark.asyncio
    async def test_send_response_formats_for_channel(self):
        result = await send_response(ResponseInput(
            ticket_id="ticket-1", message="Hello!", channel=Channel.WHATSAPP
        ))
        assert "whatsapp" in result.lower()

    @pytest.mark.asyncio
    async def test_customer_history_empty(self):
        with patch("production.agent.tools.get_customer_history_across_channels", new_callable=AsyncMock) as mock:
            from production.agent.tools import get_customer_history
            mock.return_value = []
            result = await get_customer_history("cust-new")
            assert "new customer" in result.lower() or "no previous" in result.lower()
