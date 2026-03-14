# FlowBoard - Escalation Rules

## Immediate Escalation (Priority: URGENT)
These situations MUST be escalated to a human agent immediately:

### 1. Legal/Compliance
- Customer mentions "lawyer", "legal", "sue", "attorney", "GDPR", "lawsuit"
- Any data breach or privacy concern
- Subpoena or legal document requests

### 2. Billing Disputes
- Refund requests of any amount
- Unauthorized charges
- Pricing negotiations or custom pricing requests
- Invoice discrepancies

### 3. Account Security
- Account compromise/hacking reports
- Unauthorized access claims
- Data deletion requests (GDPR right to erasure)

### 4. Angry/Abusive Customers
- Customer sentiment score below 0.3
- Use of profanity or aggressive language
- ALLCAPS messages with exclamation marks (multiple)
- Threats of any kind

### 5. Customer Request
- Customer explicitly asks for "human", "agent", "representative", "manager", "supervisor"
- On WhatsApp: customer sends "human", "agent", or "representative"
- Customer says "I don't want to talk to a bot/AI"

---

## Standard Escalation (Priority: HIGH)
Escalate within current conversation, but not immediately urgent:

### 1. Technical Issues Beyond Scope
- Server errors or outages (direct to engineering)
- Data loss or corruption reports
- API issues affecting production systems
- SSO/authentication system failures

### 2. Feature Requests from Paying Customers
- Enterprise customers requesting custom features
- Business plan customers with specific workflow needs
- Requests that require product team input

### 3. Multi-touch Issues
- Customer has contacted support 3+ times about the same issue
- Issue unresolved after 2 agent interactions
- Cross-department issues (billing + technical)

---

## Information Not Available
When the AI cannot find relevant information:

1. First attempt: Search knowledge base with alternative keywords
2. Second attempt: Try broader category search
3. After 2 failed searches: Escalate with note "Information not found in knowledge base"

---

## Escalation Process
1. Create escalation ticket with full conversation context
2. Tag with reason code (legal, billing, technical, sentiment, customer_request)
3. Include customer history across all channels
4. Notify human support team via Kafka escalation topic
5. Send customer a message: "I'm connecting you with a specialist who can better help with this."

---

## DO NOT Escalate
- General "how to" questions (answer from docs)
- Password reset requests (guide through process)
- Plan comparison questions (share feature table, but don't discuss pricing deals)
- Integration setup help (guide through steps)
- Bug reports that can be acknowledged and ticketed
