# Transition Checklist: General → Custom Agent

## 1. Discovered Requirements
- [x] Multi-channel intake (Email, WhatsApp, Web Form)
- [x] Channel-appropriate response formatting
- [x] Cross-channel customer identification (email + phone)
- [x] Conversation continuity across channels
- [x] Escalation detection (pricing, legal, sentiment, security, customer request)
- [x] Empty/unclear message handling
- [x] Multi-question email handling
- [x] Returning customer acknowledgment
- [x] Ticket creation for every interaction
- [x] Customer history lookup before responding

## 2. Working Prompts

### System Prompt That Worked:
See `production/agent/prompts.py` - Channel-aware system prompt with hard constraints, escalation triggers, and response quality standards.

### Tool Descriptions That Worked:
- Detailed docstrings explaining WHEN to use each tool
- Include channel parameter in ticket creation
- send_response tool handles channel formatting automatically

## 3. Edge Cases Found
| Edge Case | How It Was Handled | Test Case Needed |
|-----------|-------------------|------------------|
| Empty message | Ask for clarification | Yes |
| Pricing question | Escalate immediately | Yes |
| Angry + legal threat | Escalate (dual trigger) | Yes |
| "human" keyword on WhatsApp | Escalate to human | Yes |
| Account security breach | Immediate escalation | Yes |
| GDPR data deletion request | Escalate to legal | Yes |
| Duplicate billing charge | Escalate to billing | Yes |
| File exceeds 25MB limit | Answer from docs | Yes |
| Feature not on current plan | Explain limits, suggest upgrade | Yes |
| Returning customer | Acknowledge + check history | Yes |
| Multi-question email | Answer all questions | Yes |
| Account hacked report | Immediate security escalation | Yes |
| Profanity + threats | Escalate (sentiment) | Yes |
| Education/nonprofit discount | Escalate to pricing | Yes |
| Data export before cancel | Guide through process | Yes |

## 4. Response Patterns
- Email: Formal greeting > acknowledgment > detailed solution > next steps > sign-off with "FlowBoard Support Team"
- WhatsApp: Quick, casual, under 300 chars, 1-2 emojis max, "type 'human' for live support"
- Web: Semi-formal, thank for reaching out, include ticket reference

## 5. Escalation Rules (Finalized)
- Trigger 1: Pricing/billing inquiries → `pricing_inquiry`
- Trigger 2: Refund requests → `refund_request`
- Trigger 3: Legal/GDPR mentions → `legal_compliance`
- Trigger 4: Sentiment < 0.3 or profanity → `negative_sentiment`
- Trigger 5: Security/hacking reports → `security_incident`
- Trigger 6: Customer says "human"/"agent" → `customer_request`
- Trigger 7: 2 failed KB searches → `info_not_found`

## 6. Performance Baseline
From prototype testing:
- Average response time: < 3 seconds (target)
- Accuracy on test set: > 85% (target)
- Escalation rate: ~25% of sample tickets need escalation

## Pre-Transition Checklist
- [x] Working prototype that handles basic queries
- [x] Documented edge cases (15 documented)
- [x] Working system prompt
- [x] Tools defined and tested
- [x] Channel-specific response patterns identified
- [x] Escalation rules finalized
- [x] Performance baseline measured

## Transition Steps
- [x] Created production folder structure
- [ ] Extracted prompts to prompts.py
- [ ] Converted tools to @function_tool
- [ ] Added Pydantic input validation to all tools
- [ ] Added error handling to all tools
- [ ] Created transition test suite
- [ ] All transition tests passing

## Ready for Production Build
- [ ] Database schema designed
- [ ] Kafka topics defined
- [ ] Channel handlers outlined
- [ ] Kubernetes resource requirements estimated
- [ ] API endpoints listed
