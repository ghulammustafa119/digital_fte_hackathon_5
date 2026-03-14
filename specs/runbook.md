# Customer Success FTE - Incident Response Runbook

## Service Overview
- **Service**: Customer Success FTE (AI-powered customer support)
- **Channels**: Gmail (Email), WhatsApp (Twilio), Web Form
- **Infrastructure**: Kubernetes (API pods + Worker pods), PostgreSQL, Kafka
- **Health Check**: `GET /health` on API pods (port 8000)

---

## Monitoring & Alerts

### Health Check
```bash
curl https://support-api.yourdomain.com/health
```
Expected response:
```json
{"status": "healthy", "channels": {"email": "active", "whatsapp": "active", "web_form": "active"}}
```

### Key Metrics
```bash
curl https://support-api.yourdomain.com/metrics/channels
```
Monitor:
- `total_conversations` per channel
- `avg_sentiment` (alert if < 0.4)
- `escalations` count (alert if rate > 25%)

### Kubernetes Pod Health
```bash
kubectl get pods -n customer-success-fte
kubectl top pods -n customer-success-fte
```

---

## Incident Procedures

### 1. API Pods Not Responding

**Symptoms**: Health check fails, 502/503 errors from ingress

**Steps**:
1. Check pod status: `kubectl get pods -n customer-success-fte -l component=api`
2. Check pod logs: `kubectl logs -n customer-success-fte -l component=api --tail=100`
3. Check resource usage: `kubectl top pods -n customer-success-fte`
4. If OOMKilled: Increase memory limits in `deployment-api.yaml`
5. If CrashLoopBackOff: Check logs for startup errors (DB connection, missing env vars)
6. Restart pods: `kubectl rollout restart deployment/fte-api -n customer-success-fte`

### 2. Message Processing Stopped

**Symptoms**: Messages in Kafka not being consumed, customers not getting responses

**Steps**:
1. Check worker pods: `kubectl get pods -n customer-success-fte -l component=message-processor`
2. Check worker logs: `kubectl logs -n customer-success-fte -l component=message-processor --tail=100`
3. Check Kafka consumer lag:
   ```bash
   kubectl exec -n kafka kafka-0 -- kafka-consumer-groups \
     --bootstrap-server localhost:9092 \
     --group fte-message-processor \
     --describe
   ```
4. If lag is growing: Scale workers `kubectl scale deployment/fte-message-processor --replicas=5 -n customer-success-fte`
5. Check dead letter queue for failed messages:
   ```bash
   kubectl exec -n kafka kafka-0 -- kafka-console-consumer \
     --bootstrap-server localhost:9092 \
     --topic fte.dlq --from-beginning --max-messages 10
   ```

### 3. Database Connection Issues

**Symptoms**: 500 errors, "connection refused" in logs

**Steps**:
1. Check PostgreSQL pod: `kubectl get pods -n customer-success-fte -l app=postgres`
2. Check DB connections:
   ```sql
   SELECT count(*) FROM pg_stat_activity WHERE datname = 'fte_db';
   ```
3. If connection pool exhausted: Restart API/worker pods to reset pools
4. If DB is down: Check PV (persistent volume) status, restart PostgreSQL pod
5. Check disk space: `kubectl exec postgres-0 -- df -h /var/lib/postgresql/data`

### 4. Gmail Channel Down

**Symptoms**: Emails not being processed, webhook errors

**Steps**:
1. Check API logs for Gmail webhook errors
2. Verify Gmail API credentials haven't expired
3. Check Pub/Sub subscription status in Google Cloud Console
4. Re-setup push notifications:
   ```python
   await gmail_handler.setup_push_notifications("projects/PROJECT/topics/gmail-push")
   ```
5. Fallback: Gmail push notifications expire after 7 days - ensure renewal cron is active

### 5. WhatsApp Channel Down

**Symptoms**: WhatsApp messages not being received/sent

**Steps**:
1. Check Twilio Dashboard for service status
2. Verify webhook URL is correctly configured in Twilio Console
3. Check API logs for Twilio signature validation failures
4. Verify Twilio credentials (Account SID, Auth Token) in secrets
5. Test sending: Use Twilio API Explorer to send a test message
6. If sandbox expired: Rejoin Twilio WhatsApp Sandbox

### 6. High Escalation Rate (>25%)

**Symptoms**: Metrics show escalation rate exceeding threshold

**Steps**:
1. Check escalation reasons distribution:
   ```sql
   SELECT escalation_reason, COUNT(*) FROM tickets
   WHERE status = 'escalated' AND created_at > NOW() - INTERVAL '24 hours'
   GROUP BY escalation_reason ORDER BY count DESC;
   ```
2. If `info_not_found` is high: Knowledge base may need updating, run seed script
3. If `negative_sentiment` is high: Review recent conversations for product issues
4. If `pricing_inquiry` is high: Normal - these always escalate by design
5. Update knowledge base if needed:
   ```bash
   python -m production.database.seed_knowledge_base
   ```

### 7. Kafka Broker Down

**Symptoms**: Messages not flowing, producer/consumer errors

**Steps**:
1. Check Kafka pods: `kubectl get pods -n kafka`
2. Check broker status:
   ```bash
   kubectl exec kafka-0 -n kafka -- kafka-broker-api-versions --bootstrap-server localhost:9092
   ```
3. Check topic health:
   ```bash
   kubectl exec kafka-0 -n kafka -- kafka-topics --describe --bootstrap-server localhost:9092
   ```
4. If broker is down: Restart Kafka pod, messages in Kafka are persisted on disk
5. After Kafka recovery: Restart worker pods to reconnect consumers

---

## Scaling Procedures

### Scale API Pods
```bash
kubectl scale deployment/fte-api --replicas=N -n customer-success-fte
```

### Scale Worker Pods
```bash
kubectl scale deployment/fte-message-processor --replicas=N -n customer-success-fte
```

### HPA is configured to auto-scale at 70% CPU:
- API: 3 min → 20 max pods
- Workers: 3 min → 30 max pods

---

## Recovery Procedures

### Full System Restart
```bash
kubectl rollout restart deployment/fte-api -n customer-success-fte
kubectl rollout restart deployment/fte-message-processor -n customer-success-fte
```

### Database Recovery
1. Check if WAL replay is needed
2. Restore from backup if data corrupted
3. Re-run migrations: `psql -f production/database/schema.sql`
4. Re-seed knowledge base: `python -m production.database.seed_knowledge_base`

### Re-process Failed Messages
```bash
# Read from DLQ and republish to incoming
kubectl exec kafka-0 -n kafka -- kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic fte.dlq --from-beginning > /tmp/failed_messages.json

# Review and republish valid messages to fte.tickets.incoming
```

---

## Contact & Escalation

| Level | Who | When |
|-------|-----|------|
| L1 | On-call engineer | Any alert fires |
| L2 | Platform team | Infrastructure issues (K8s, Kafka, DB) |
| L3 | AI/ML team | Agent accuracy issues, prompt changes |
| External | Twilio Support | WhatsApp delivery failures |
| External | Google Support | Gmail API issues |
