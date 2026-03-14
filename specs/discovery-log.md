# Discovery Log - Customer Success FTE for FlowBoard

## Exploration Summary
**Date**: 2026-03-14
**Product**: FlowBoard - Cloud-based project management SaaS
**Objective**: Build a 24/7 AI Customer Success agent across Email, WhatsApp, and Web Form channels

---

## 1. Sample Ticket Analysis (55 tickets analyzed)

### Channel Distribution
| Channel | Count | Percentage |
|---------|-------|------------|
| Email | 20 | 36% |
| WhatsApp | 18 | 33% |
| Web Form | 17 | 31% |

### Category Breakdown
| Category | Count | Notes |
|----------|-------|-------|
| General/How-to | 25 | Most common - product usage questions |
| Technical/Bug | 16 | Integration issues, app crashes, sync problems |
| Billing | 8 | Pricing, refunds, plan changes |
| Feedback | 3 | Feature requests, suggestions |
| Security | 3 | Account compromise, data breach concerns |

### Priority Distribution
| Priority | Count |
|----------|-------|
| Low | 22 |
| Medium | 18 |
| High | 15 |

---

## 2. Channel-Specific Patterns Discovered

### Email Patterns
- Messages are **longer and more detailed** (avg 50-100 words)
- Often include context, history, and multiple questions in one message
- Customers expect formal, structured responses
- Subject lines provide useful context for categorization
- Thread-based conversations (Gmail thread_id enables continuity)

### WhatsApp Patterns
- Messages are **very short** (avg 5-15 words)
- Casual tone, lowercase, minimal punctuation
- Customers expect **instant, brief** responses
- Special keywords: "human", "agent" = escalation triggers
- Empty messages occur (ticket #54) - need handling
- Follow-up messages are common in same conversation

### Web Form Patterns
- **Most structured** input (name, email, subject, category, message)
- Message length is moderate (30-80 words)
- Category field helps with auto-triage
- Customers expect email follow-up after submission
- Priority self-selection by customer (but may not be accurate)

---

## 3. Key Requirements Discovered

### R1: Cross-Channel Customer Identification
- Email address is primary identifier (email + web form)
- Phone number identifies WhatsApp users
- Same customer may contact via multiple channels
- Must merge history: e.g., customer emails first, then WhatsApps about same issue

### R2: Channel-Appropriate Response Formatting
- Email: Greeting + detailed answer + sign-off (~500 words max)
- WhatsApp: Short, conversational (~300 chars preferred, 1600 max)
- Web Form: Semi-formal + link to ticket status (~300 words max)

### R3: Escalation Detection
- Pricing/billing inquiries → always escalate
- Legal mentions ("lawyer", "sue", "GDPR") → immediate escalation
- Negative sentiment / profanity → escalate
- Explicit request ("human", "agent") → escalate
- Security concerns → immediate escalation
- 2 failed knowledge base searches → escalate

### R4: Empty/Unclear Message Handling
- WhatsApp ticket #54 has empty message
- Agent must ask for clarification, not crash
- "Hi" or single-word messages need prompting

### R5: Multi-Question Handling
- Email tickets often contain 2-3 questions in one message
- Agent must address ALL questions, not just the first one

### R6: Returning Customer Context
- Ticket #51: "thanks for the help last time! now i have another question"
- Agent should acknowledge prior interactions
- Must check history across ALL channels

---

## 4. Edge Cases Documented

| # | Edge Case | Channel | Example | Handling Strategy |
|---|-----------|---------|---------|-------------------|
| 1 | Empty message | WhatsApp | Ticket #54 | Ask for clarification |
| 2 | Pricing question | Email | Ticket #4 | Escalate immediately |
| 3 | Angry + legal threat | Email | Ticket #22 | Escalate (sentiment + legal) |
| 4 | Single word "human" | WhatsApp | Ticket #13 | Escalate to human agent |
| 5 | Security breach report | Email | Ticket #50 | Immediate escalation |
| 6 | GDPR data deletion | Email | Ticket #14 | Escalate to legal/compliance |
| 7 | Duplicate billing charge | Email | Ticket #9 | Escalate to billing |
| 8 | File too large | Web Form | Ticket #7 | Answer from docs (25MB limit) |
| 9 | Feature not on plan | Multiple | Ticket #11 | Explain plan limits, suggest upgrade |
| 10 | Returning customer | WhatsApp | Ticket #51 | Acknowledge + check history |
| 11 | Multi-question email | Email | Ticket #28 | Answer all questions |
| 12 | Account hacked | WhatsApp | Ticket #27 | Immediate security escalation |
| 13 | Profanity + threats | WhatsApp | Ticket #46 | Escalate (sentiment) |
| 14 | Education/nonprofit discount | Web Form | Ticket #23, #30 | Escalate to pricing |
| 15 | Data export before cancel | Email | Ticket #20 | Guide through process |

---

## 5. Tool Requirements Identified

| Tool | Purpose | Used When |
|------|---------|-----------|
| `search_knowledge_base` | Search product docs | Customer asks product questions |
| `create_ticket` | Log every interaction | Start of every conversation |
| `get_customer_history` | Check past interactions | Every incoming message |
| `escalate_to_human` | Hand off complex issues | Escalation triggers detected |
| `send_response` | Reply via correct channel | Every response |

---

## 6. Performance Targets
- Response processing time: < 3 seconds
- End-to-end delivery: < 30 seconds
- Accuracy on test set: > 85%
- Escalation rate: < 20% (based on sample: ~25% need escalation)
- Cross-channel customer identification: > 95%
- Uptime: > 99.9%

---

## 7. Technology Decisions
| Component | Choice | Reason |
|-----------|--------|--------|
| Agent Framework | OpenAI Agents SDK | Required by hackathon |
| API | FastAPI | Async, fast, Pydantic validation |
| Database | PostgreSQL + pgvector | CRM system + semantic search |
| Streaming | Apache Kafka | Multi-channel event processing |
| Email | Gmail API + Pub/Sub | Real-time email intake |
| WhatsApp | Twilio WhatsApp API | Reliable, sandbox available |
| Web Form | React/Next.js | Required deliverable |
| Deployment | Kubernetes | Scalability, auto-healing |
