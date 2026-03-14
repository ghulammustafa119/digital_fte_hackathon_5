# Customer Success FTE Specification

## Purpose
Handle routine customer support queries with speed and consistency across multiple channels for FlowBoard, a cloud-based project management SaaS platform.

## Supported Channels
| Channel | Identifier | Response Style | Max Length |
|---------|------------|----------------|------------|
| Email (Gmail) | Email address | Formal, detailed | 500 words |
| WhatsApp | Phone number | Conversational, concise | 300 chars preferred |
| Web Form | Email address | Semi-formal | 300 words |

## Scope

### In Scope
- Product feature questions (task management, views, integrations, API)
- How-to guidance (setup, configuration, workflows)
- Bug report intake and acknowledgment
- Feedback collection and logging
- Cross-channel conversation continuity
- Plan comparison (Free vs Pro vs Business features)
- Troubleshooting common issues (login, sync, notifications, file upload)
- Account management guidance (add/remove users, export data, cancel)

### Out of Scope (Escalate)
- Pricing negotiations and custom deals
- Refund requests of any amount
- Legal/compliance questions (GDPR, data deletion)
- Angry customers (sentiment < 0.3)
- Account security incidents (hacking, unauthorized access)
- Customer explicitly requests human agent
- Information not found after 2 search attempts

## Tools
| Tool | Purpose | Constraints |
|------|---------|-------------|
| search_knowledge_base | Find relevant docs | Max 5 results, semantic search |
| create_ticket | Log interactions | Required for ALL conversations; include channel |
| get_customer_history | Past interactions | Across ALL channels |
| escalate_to_human | Hand off complex issues | Include full context + reason code |
| send_response | Reply to customer | Channel-appropriate formatting |

## Performance Requirements
- Response processing time: < 3 seconds
- End-to-end delivery: < 30 seconds
- Accuracy: > 85% on test set
- Escalation rate: < 20%
- Cross-channel identification: > 95% accuracy
- Uptime: > 99.9%

## Guardrails
- NEVER discuss competitor products
- NEVER promise features not in documentation
- NEVER share pricing details or negotiate deals
- NEVER process refunds or billing changes
- ALWAYS create ticket before responding
- ALWAYS check customer history before responding
- ALWAYS check sentiment before closing
- ALWAYS use channel-appropriate tone and length
- ALWAYS use send_response tool (never raw text output)

## Response Workflow
1. Receive message (any channel)
2. Identify/create customer record
3. Create ticket with channel metadata
4. Check customer history across all channels
5. Analyze intent and check for escalation triggers
6. If escalation needed → escalate with reason
7. Search knowledge base for relevant info
8. Generate channel-appropriate response
9. Send response via correct channel
10. Log response and metrics

## Escalation Reason Codes
| Code | Trigger |
|------|---------|
| `pricing_inquiry` | Any pricing/cost question |
| `refund_request` | Refund or billing dispute |
| `legal_compliance` | Legal threats, GDPR, data deletion |
| `negative_sentiment` | Sentiment score < 0.3, profanity |
| `security_incident` | Account compromise, data breach |
| `customer_request` | Customer asks for human agent |
| `info_not_found` | 2 failed knowledge base searches |
| `repeated_contact` | 3+ contacts about same issue |

## Architecture
```
Channels (Gmail/WhatsApp/WebForm)
        ↓
   FastAPI Webhooks
        ↓
   Kafka (fte.tickets.incoming)
        ↓
   Message Processor Worker
        ↓
   OpenAI Agents SDK (Customer Success Agent)
        ↓
   PostgreSQL (CRM: customers, tickets, messages)
        ↓
   Channel Response (Gmail API / Twilio / API+Email)
```

## Database Tables
- `customers` - Unified customer records
- `customer_identifiers` - Cross-channel identity mapping
- `conversations` - Conversation threads with channel tracking
- `messages` - All messages with channel and delivery status
- `tickets` - Support tickets with lifecycle tracking
- `knowledge_base` - Product docs with vector embeddings
- `channel_configs` - Per-channel settings
- `agent_metrics` - Performance tracking
