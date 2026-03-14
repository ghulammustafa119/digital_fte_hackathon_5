# Customer Success Digital FTE - FlowBoard

A 24/7 AI-powered Customer Success agent (Digital FTE) for **FlowBoard**, a cloud-based project management SaaS platform. Built with OpenAI Agents SDK, FastAPI, PostgreSQL, Kafka, and Kubernetes.

## Architecture

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│    Gmail     │  │   WhatsApp   │  │   Web Form   │
│   (Email)    │  │   (Twilio)   │  │  (Next.js)   │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       └─────────────────┼─────────────────┘
                         ▼
              ┌─────────────────┐
              │    FastAPI      │
              │   Webhooks      │
              └────────┬────────┘
                       ▼
              ┌─────────────────┐
              │     Kafka       │
              │  (Event Bus)    │
              └────────┬────────┘
                       ▼
              ┌─────────────────┐     ┌──────────┐
              │  Agent Worker   │────▶│ Postgres │
              │ (OpenAI SDK)    │     │(pgvector)│
              └────────┬────────┘     └──────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   Reply via      Reply via      Reply via
    Gmail          Twilio        API/Email
```

## Features

- **Multi-Channel Support**: Gmail, WhatsApp (Twilio), Web Form
- **AI Agent**: OpenAI Agents SDK with 5 tools (search KB, create ticket, get history, escalate, send response)
- **Cross-Channel Continuity**: Identifies customers across channels, merges conversation history
- **Smart Escalation**: Auto-detects pricing, legal, sentiment, security triggers
- **Channel-Aware Responses**: Email (formal), WhatsApp (concise), Web (semi-formal)
- **CRM System**: PostgreSQL-based ticket management (customers, conversations, tickets, messages)
- **Semantic Search**: pgvector for knowledge base similarity search
- **Event Streaming**: Kafka for async multi-channel message processing
- **Auto-Scaling**: Kubernetes with HPA (API: 3-20 pods, Workers: 3-30 pods)
- **Monitoring**: Channel-specific metrics, health checks, delivery tracking

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Agent | OpenAI Agents SDK (GPT-4o) |
| API | FastAPI (Python) |
| Database | PostgreSQL 16 + pgvector |
| Streaming | Apache Kafka |
| Email | Gmail API + Pub/Sub |
| WhatsApp | Twilio WhatsApp API |
| Web Form | Next.js + React + Tailwind CSS |
| Deployment | Kubernetes + Docker |
| Testing | pytest, Locust |

## Project Structure

```
├── context/                    # Company context for the AI agent
│   ├── company-profile.md      # FlowBoard company details
│   ├── product-docs.md         # Product documentation
│   ├── sample-tickets.json     # 55 sample tickets (3 channels)
│   ├── escalation-rules.md     # Escalation trigger rules
│   └── brand-voice.md          # Channel-wise tone guide
├── specs/                      # Incubation deliverables
│   ├── discovery-log.md        # Requirements discovered
│   ├── customer-success-fte-spec.md
│   └── transition-checklist.md
├── src/web-form/               # Next.js Web Support Form
│   ├── components/SupportForm.tsx
│   └── app/
├── production/
│   ├── agent/                  # OpenAI Agents SDK agent
│   ├── channels/               # Gmail, WhatsApp, Web handlers
│   ├── api/main.py             # FastAPI application
│   ├── workers/                # Kafka message processor
│   ├── kafka_client.py         # Kafka producer/consumer
│   ├── database/               # Schema + queries
│   ├── k8s/                    # Kubernetes manifests
│   └── tests/                  # Unit, E2E, load tests
├── docker-compose.yml          # Local dev (Postgres + Kafka + App)
├── Dockerfile
└── requirements.txt
```

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.12+
- Node.js 18+ (for web form)
- OpenAI API key

### 1. Clone & Setup

```bash
git clone https://github.com/ghulammustafa119/digital_fte_hackathon_5.git
cd digital_fte_hackathon_5
cp .env.example .env
# Edit .env with your API keys
```

### 2. Start Infrastructure

```bash
docker-compose up -d postgres kafka zookeeper kafka-init
```

### 3. Install Dependencies & Run API

```bash
pip install -r requirements.txt
uvicorn production.api.main:app --reload --port 8000
```

### 4. Start Message Processor

```bash
python -m production.workers.message_processor
```

### 5. Start Web Form (Optional)

```bash
cd src/web-form
npm install
npm run dev
```

### 6. Run Everything with Docker

```bash
docker-compose up --build
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/support/submit` | POST | Web form submission |
| `/support/ticket/{id}` | GET | Ticket status |
| `/webhooks/gmail` | POST | Gmail Pub/Sub webhook |
| `/webhooks/whatsapp` | POST | Twilio WhatsApp webhook |
| `/webhooks/whatsapp/status` | POST | WhatsApp delivery status |
| `/customers/lookup` | GET | Customer lookup (email/phone) |
| `/conversations/{id}` | GET | Conversation history |
| `/metrics/channels` | GET | Per-channel metrics |

## Testing

```bash
# Unit & channel tests
pytest production/tests/test_agent.py -v
pytest production/tests/test_channels.py -v

# E2E tests (requires running API)
pytest production/tests/test_e2e.py -v

# Load test
locust -f production/tests/load_test.py --host=http://localhost:8000
```

## Kubernetes Deployment

```bash
kubectl apply -f production/k8s/namespace.yaml
kubectl apply -f production/k8s/configmap.yaml
kubectl apply -f production/k8s/secrets.yaml
kubectl apply -f production/k8s/deployment-api.yaml
kubectl apply -f production/k8s/deployment-worker.yaml
kubectl apply -f production/k8s/service.yaml
kubectl apply -f production/k8s/ingress.yaml
kubectl apply -f production/k8s/hpa.yaml
```

## Kafka Topics

| Topic | Purpose |
|-------|---------|
| `fte.tickets.incoming` | All incoming messages (unified) |
| `fte.channels.email.inbound` | Email-specific inbound |
| `fte.channels.whatsapp.inbound` | WhatsApp-specific inbound |
| `fte.channels.webform.inbound` | Web form-specific inbound |
| `fte.escalations` | Escalated tickets |
| `fte.metrics` | Performance metrics |
| `fte.dlq` | Dead letter queue |

## Database Schema

8 tables: `customers`, `customer_identifiers`, `conversations`, `messages`, `tickets`, `knowledge_base`, `channel_configs`, `agent_metrics`

See full schema: [`production/database/schema.sql`](production/database/schema.sql)

## Performance Targets

- Response processing: < 3 seconds
- End-to-end delivery: < 30 seconds
- Accuracy: > 85%
- Escalation rate: < 20%
- Cross-channel identification: > 95%
- Uptime: > 99.9%
