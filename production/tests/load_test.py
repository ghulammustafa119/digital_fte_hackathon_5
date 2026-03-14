"""Load testing with Locust for Customer Success FTE API."""

from locust import HttpUser, task, between
import random
import uuid


class WebFormUser(HttpUser):
    """Simulate users submitting support forms."""
    wait_time = between(2, 10)
    weight = 3

    @task
    def submit_support_form(self):
        categories = ["general", "technical", "billing", "feedback", "bug_report"]
        self.client.post("/support/submit", json={
            "name": f"Load Test User {random.randint(1, 10000)}",
            "email": f"loadtest-{uuid.uuid4()}@example.com",
            "subject": f"Load Test Query {random.randint(1, 100)}",
            "category": random.choice(categories),
            "message": "This is a load test message to verify system performance under stress.",
        })


class HealthCheckUser(HttpUser):
    """Monitor system health during load test."""
    wait_time = between(5, 15)
    weight = 1

    @task
    def check_health(self):
        self.client.get("/health")

    @task
    def check_metrics(self):
        self.client.get("/metrics/channels")
