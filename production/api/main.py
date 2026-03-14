"""FastAPI application for Customer Success FTE - Multi-channel support API."""

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import logging

from production.channels.gmail_handler import GmailHandler
from production.channels.whatsapp_handler import WhatsAppHandler
from production.channels.web_form_handler import router as web_form_router
from production.kafka_client import FTEKafkaProducer, TOPICS
from production.database.queries import (
    get_db_pool,
    close_db_pool,
    find_customer_by_email,
    find_customer_by_phone,
    get_channel_metrics,
    get_conversation_messages,
    update_delivery_status,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Customer Success FTE API",
    description="24/7 AI-powered customer support across Email, WhatsApp, and Web",
    version="2.0.0",
)

# CORS for web form
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include web form router
app.include_router(web_form_router)

# Initialize handlers
gmail_handler = GmailHandler()
whatsapp_handler = WhatsAppHandler()
kafka_producer = FTEKafkaProducer()


@app.on_event("startup")
async def startup():
    await get_db_pool()
    try:
        await kafka_producer.start()
    except Exception as e:
        logger.warning(f"Kafka producer not available: {e}")
    await gmail_handler.initialize()
    await whatsapp_handler.initialize()
    logger.info("FTE API started successfully")


@app.on_event("shutdown")
async def shutdown():
    await kafka_producer.stop()
    await close_db_pool()
    logger.info("FTE API shut down")


# ---- Health Check ----

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "channels": {
            "email": "active",
            "whatsapp": "active",
            "web_form": "active",
        },
    }


# ---- Gmail Webhook ----

@app.post("/webhooks/gmail")
async def gmail_webhook(request: Request, background_tasks: BackgroundTasks):
    """Handle Gmail push notifications via Pub/Sub."""
    try:
        body = await request.json()
        messages = await gmail_handler.process_notification(body)

        for message in messages:
            background_tasks.add_task(
                kafka_producer.publish, TOPICS["tickets_incoming"], message
            )

        return {"status": "processed", "count": len(messages)}

    except Exception as e:
        logger.error(f"Gmail webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---- WhatsApp Webhook ----

@app.post("/webhooks/whatsapp")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    """Handle incoming WhatsApp messages via Twilio webhook."""
    form_data = await request.form()
    params = dict(form_data)

    # Validate Twilio signature
    signature = request.headers.get("X-Twilio-Signature", "")
    url = str(request.url)
    if not await whatsapp_handler.validate_webhook(url, params, signature):
        raise HTTPException(status_code=403, detail="Invalid signature")

    message = await whatsapp_handler.process_webhook(params)

    background_tasks.add_task(
        kafka_producer.publish, TOPICS["tickets_incoming"], message
    )

    # Return empty TwiML (agent will respond asynchronously)
    return Response(
        content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
        media_type="application/xml",
    )


@app.post("/webhooks/whatsapp/status")
async def whatsapp_status_webhook(request: Request):
    """Handle WhatsApp message status updates (delivered, read, etc.)."""
    form_data = await request.form()

    channel_message_id = form_data.get("MessageSid")
    status = form_data.get("MessageStatus")

    if channel_message_id and status:
        await update_delivery_status(channel_message_id, status)

    return {"status": "received"}


# ---- Conversation & Customer APIs ----

@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get full conversation history with cross-channel context."""
    messages = await get_conversation_messages(conversation_id)
    if not messages:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"conversation_id": conversation_id, "messages": messages}


@app.get("/customers/lookup")
async def lookup_customer(email: str = None, phone: str = None):
    """Look up customer by email or phone across all channels."""
    if not email and not phone:
        raise HTTPException(status_code=400, detail="Provide email or phone")

    customer = None
    if email:
        customer = await find_customer_by_email(email)
    if not customer and phone:
        customer = await find_customer_by_phone(phone)

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    return customer


# ---- Metrics ----

@app.get("/metrics/channels")
async def get_metrics_by_channel():
    """Get performance metrics by channel."""
    metrics = await get_channel_metrics()
    return {row["channel"]: row for row in metrics}
