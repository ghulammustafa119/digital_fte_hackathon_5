"""End-to-end tests for the Customer Success FTE API."""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from datetime import datetime

BASE_URL = "http://localhost:8000"


@pytest.fixture
async def client():
    async with AsyncClient(base_url=BASE_URL) as ac:
        yield ac


class TestWebFormChannel:

    @pytest.mark.asyncio
    async def test_form_submission(self, client):
        response = await client.post("/support/submit", json={
            "name": "Test User", "email": "test@example.com",
            "subject": "Help with API", "category": "technical",
            "message": "I need help with the API authentication"
        })
        assert response.status_code == 200
        data = response.json()
        assert "ticket_id" in data
        assert data["message"] is not None

    @pytest.mark.asyncio
    async def test_form_validation_rejects_invalid(self, client):
        response = await client.post("/support/submit", json={
            "name": "A", "email": "invalid", "subject": "Hi",
            "category": "invalid", "message": "Short"
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_ticket_status_not_found(self, client):
        response = await client.get("/support/ticket/nonexistent-id")
        assert response.status_code == 404


class TestHealthAndMetrics:

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "email" in data["channels"]
        assert "whatsapp" in data["channels"]
        assert "web_form" in data["channels"]

    @pytest.mark.asyncio
    async def test_metrics_endpoint(self, client):
        response = await client.get("/metrics/channels")
        assert response.status_code == 200


class TestCustomerLookup:

    @pytest.mark.asyncio
    async def test_lookup_without_params_fails(self, client):
        response = await client.get("/customers/lookup")
        assert response.status_code == 400
