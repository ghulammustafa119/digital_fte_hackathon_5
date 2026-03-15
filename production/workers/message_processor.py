"""Unified message processor - Kafka consumer that routes messages to the FTE agent."""

from dotenv import load_dotenv
load_dotenv()

import asyncio
from datetime import datetime
import logging

from agents import Runner

from production.kafka_client import FTEKafkaConsumer, FTEKafkaProducer, TOPICS
from production.agent.customer_success_agent import customer_success_agent
from production.agent.tools import Channel
from production.channels.gmail_handler import GmailHandler
from production.channels.whatsapp_handler import WhatsAppHandler
from production.database.queries import (
    find_customer_by_email,
    find_customer_by_phone,
    create_customer,
    get_active_conversation,
    create_conversation,
    store_message,
    get_conversation_messages,
    record_metric,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class UnifiedMessageProcessor:
    """Process incoming messages from all channels through the FTE agent."""

    def __init__(self):
        self.gmail = GmailHandler()
        self.whatsapp = WhatsAppHandler()
        self.producer = FTEKafkaProducer()

    async def start(self):
        """Start the message processor."""
        await self.producer.start()
        await self.gmail.initialize()
        await self.whatsapp.initialize()

        consumer = FTEKafkaConsumer(
            topics=[TOPICS["tickets_incoming"]],
            group_id="fte-message-processor",
        )
        await consumer.start()

        logger.info("Message processor started, listening for tickets...")

        try:
            await consumer.consume(self.process_message)
        finally:
            await consumer.stop()
            await self.producer.stop()

    async def process_message(self, topic: str, message: dict):
        """Process a single incoming message from any channel."""
        try:
            start_time = datetime.utcnow()
            channel = Channel(message["channel"])

            # Resolve customer
            customer_id = await self.resolve_customer(message)

            # Get or create conversation
            conversation_id = await self.get_or_create_conversation(customer_id, channel)

            # Store incoming message
            await store_message(
                conversation_id=conversation_id,
                channel=channel.value,
                direction="inbound",
                role="customer",
                content=message.get("content", ""),
                channel_message_id=message.get("channel_message_id"),
            )

            # Load conversation history for context
            history = await get_conversation_messages(conversation_id)
            agent_messages = [
                {"role": "user" if m["role"] == "customer" else "assistant", "content": m["content"]}
                for m in history
            ]

            # Run agent
            result = await Runner.run(
                customer_success_agent,
                input=agent_messages,
                context={
                    "customer_id": customer_id,
                    "conversation_id": conversation_id,
                    "channel": channel.value,
                    "ticket_subject": message.get("subject", "Support Request"),
                    "metadata": message.get("metadata", {}),
                },
            )

            # Calculate latency
            latency_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            # Store agent response
            await store_message(
                conversation_id=conversation_id,
                channel=channel.value,
                direction="outbound",
                role="agent",
                content=result.final_output,
                latency_ms=latency_ms,
            )

            # Publish metrics
            await self.producer.publish(
                TOPICS["metrics"],
                {
                    "event_type": "message_processed",
                    "channel": channel.value,
                    "customer_id": customer_id,
                    "latency_ms": latency_ms,
                },
            )

            await record_metric("response_latency_ms", latency_ms, channel=channel.value)

            logger.info(f"Processed {channel.value} message in {latency_ms}ms")

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            await self.handle_error(message, e)

    async def resolve_customer(self, message: dict) -> str:
        """Resolve or create customer from message identifiers."""
        email = message.get("customer_email")
        if email:
            customer = await find_customer_by_email(email)
            if customer:
                return str(customer["id"])
            return await create_customer(
                email=email,
                name=message.get("customer_name", ""),
            )

        phone = message.get("customer_phone")
        if phone:
            customer = await find_customer_by_phone(phone)
            if customer:
                return str(customer["id"])
            return await create_customer(phone=phone)

        raise ValueError("Could not resolve customer: no email or phone provided")

    async def get_or_create_conversation(self, customer_id: str, channel: Channel) -> str:
        """Get active conversation or create new one."""
        active = await get_active_conversation(customer_id)
        if active:
            return active
        return await create_conversation(customer_id, channel.value)

    async def handle_error(self, message: dict, error: Exception):
        """Handle processing errors gracefully."""
        channel = Channel(message.get("channel", "web_form"))
        apology = "I'm sorry, I'm having trouble processing your request right now. A human agent will follow up shortly."

        try:
            if channel == Channel.EMAIL and message.get("customer_email"):
                await self.gmail.send_reply(
                    to_email=message["customer_email"],
                    subject=message.get("subject", "Support Request"),
                    body=apology,
                )
            elif channel == Channel.WHATSAPP and message.get("customer_phone"):
                await self.whatsapp.send_message(
                    to_phone=message["customer_phone"],
                    body=apology,
                )
        except Exception as e:
            logger.error(f"Failed to send error response: {e}")

        # Publish to DLQ
        try:
            await self.producer.publish(
                TOPICS["dlq"],
                {
                    "event_type": "processing_error",
                    "original_message": message,
                    "error": str(error),
                    "requires_human": True,
                },
            )
        except Exception:
            pass


async def main():
    processor = UnifiedMessageProcessor()
    await processor.start()


if __name__ == "__main__":
    asyncio.run(main())
