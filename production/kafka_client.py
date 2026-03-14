"""Kafka client for multi-channel event streaming."""

from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
import json
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

# Topic definitions for multi-channel FTE
TOPICS = {
    "tickets_incoming": "fte.tickets.incoming",
    "email_inbound": "fte.channels.email.inbound",
    "whatsapp_inbound": "fte.channels.whatsapp.inbound",
    "webform_inbound": "fte.channels.webform.inbound",
    "email_outbound": "fte.channels.email.outbound",
    "whatsapp_outbound": "fte.channels.whatsapp.outbound",
    "escalations": "fte.escalations",
    "metrics": "fte.metrics",
    "dlq": "fte.dlq",
}


class FTEKafkaProducer:
    def __init__(self):
        self.producer = None

    async def start(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
        )
        await self.producer.start()
        logger.info("Kafka producer started")

    async def stop(self):
        if self.producer:
            await self.producer.stop()
            logger.info("Kafka producer stopped")

    async def publish(self, topic: str, event: dict):
        event["timestamp"] = datetime.utcnow().isoformat()
        await self.producer.send_and_wait(topic, event)
        logger.debug(f"Published to {topic}: {event.get('event_type', 'unknown')}")


class FTEKafkaConsumer:
    def __init__(self, topics: list, group_id: str):
        self.topics = topics
        self.group_id = group_id
        self.consumer = None

    async def start(self):
        self.consumer = AIOKafkaConsumer(
            *self.topics,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id=self.group_id,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        )
        await self.consumer.start()
        logger.info(f"Kafka consumer started for topics: {self.topics}")

    async def stop(self):
        if self.consumer:
            await self.consumer.stop()
            logger.info("Kafka consumer stopped")

    async def consume(self, handler):
        async for msg in self.consumer:
            try:
                await handler(msg.topic, msg.value)
            except Exception as e:
                logger.error(f"Error processing message from {msg.topic}: {e}")
