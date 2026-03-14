"""Tests for channel handlers (Gmail, WhatsApp, Web Form)."""

import pytest
from production.channels.whatsapp_handler import WhatsAppHandler
from production.channels.gmail_handler import GmailHandler
from production.channels.web_form_handler import SupportFormSubmission


class TestWhatsAppFormatting:

    def test_short_message_single_part(self):
        handler = WhatsAppHandler()
        result = handler.format_response("Short message")
        assert len(result) == 1
        assert result[0] == "Short message"

    def test_long_message_splits(self):
        handler = WhatsAppHandler()
        long_msg = "This is a sentence. " * 100
        result = handler.format_response(long_msg)
        assert len(result) > 1
        for part in result:
            assert len(part) <= 1600


class TestGmailExtraction:

    def test_extract_email_with_name(self):
        handler = GmailHandler()
        assert handler._extract_email("John Doe <john@example.com>") == "john@example.com"

    def test_extract_email_plain(self):
        handler = GmailHandler()
        assert handler._extract_email("john@example.com") == "john@example.com"

    def test_extract_name(self):
        handler = GmailHandler()
        assert handler._extract_name("John Doe <john@example.com>") == "John Doe"

    def test_extract_name_no_name(self):
        handler = GmailHandler()
        assert handler._extract_name("john@example.com") == ""


class TestWebFormValidation:

    def test_valid_form(self):
        form = SupportFormSubmission(
            name="John Doe", email="john@example.com",
            subject="Help with product", category="technical",
            message="I need help with the product feature"
        )
        assert form.name == "John Doe"

    def test_short_name_fails(self):
        with pytest.raises(ValueError, match="at least 2"):
            SupportFormSubmission(
                name="J", email="test@example.com",
                subject="Help needed", category="general",
                message="This is a test message"
            )

    def test_short_message_fails(self):
        with pytest.raises(ValueError, match="at least 10"):
            SupportFormSubmission(
                name="John", email="test@example.com",
                subject="Help needed", category="general",
                message="short"
            )

    def test_invalid_category_fails(self):
        with pytest.raises(ValueError, match="must be one of"):
            SupportFormSubmission(
                name="John", email="test@example.com",
                subject="Help needed", category="invalid",
                message="This is a valid message"
            )

    def test_all_valid_categories(self):
        for cat in ["general", "technical", "billing", "feedback", "bug_report"]:
            form = SupportFormSubmission(
                name="John", email="test@example.com",
                subject="Test subject", category=cat,
                message="This is a valid message"
            )
            assert form.category == cat
