# ShipAgent - Agentic Order Intelligence System

ShipAgent is a FastAPI + LangGraph order intelligence backend for detecting stuck shipments, high RTO risk, SLA breaches, and payment anomalies. It uses PostgreSQL with pgvector for RAG, Redis for scheduling support, Claude for classification and summaries, OpenAI for fallback and embeddings, and Twilio WhatsApp for merchant alerts.

The repo is designed to run locally before paid credentials are configured. `SHIPAGENT_OFFLINE_MODE=true` uses deterministic local LLM and embedding fallbacks while preserving the production code paths and model names.

For interview prep and the project walkthrough, see [INTERVIEW_PREP.md](INTERVIEW_PREP.md).

For current completion status against the original sprint checklist, see [PROGRESS.md](PROGRESS.md).

## Architecture

```text
Scheduled trigger (every 5 min)
        |
poll_orders_node (PostgreSQL query)
        |
classify_anomaly_node
  |-- RAG: pgvector cosine search -> courier policies + historical cases
  `-- Claude Haiku classification (fast + cheap, RAG context injected)
        |
route_anomaly_node (conditional edges, no LLM)
        |
+---------------------------------------------+
| STUCK_ORDER     -> resolve_stuck_node        |
| HIGH_RTO_RISK   -> assess_rto_node (Sonnet)  |
| SLA_BREACH      -> send_alert_node (Sonnet)  |
| PAYMENT_ANOMALY -> escalate_node             |
| NORMAL          -> log_decision_node         |
+---------------------------------------------+
        |
send_alert_node (Claude Sonnet -> Twilio WhatsApp)
        |
log_decision_node (PostgreSQL audit trail)
        |
END
```

## Quick Start

1. Copy env values:

```bash
cp .env.example .env
```

2. Start PostgreSQL with pgvector and Redis:

```bash
docker compose up postgres redis -d
```

3. Install Python dependencies:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

4. Seed demo data:

```bash
python scripts/seed_knowledge.py
python tests/seed_orders.py
```

5. Start the API:

```bash
uvicorn api.main:app --reload
```

6. Exercise the system:

```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/agent/run
curl http://localhost:8000/agent/decisions
curl http://localhost:8000/orders/
curl http://localhost:8000/alerts/
```

## API

- `GET /health` - service health check
- `GET /orders/` - recent orders
- `GET /orders/{order_id}` - one order
- `GET /alerts/` - recent WhatsApp alert history
- `POST /agent/run` - run one agent cycle
- `GET /agent/decisions` - recent audit log

## Demo Evidence

After running the local demo, capture:

- WhatsApp alert received from Twilio sandbox
- `/agent/decisions` response showing the audit trail
- `/orders/` response showing seeded orders and updated status

In offline mode, Twilio sends are logged to the console and persisted in `alerts` with status `sent`.

## Production Credentials

Set these in `.env`:

- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_WHATSAPP_FROM`
- `MERCHANT_WHATSAPP_TO`

Then set:

```env
SHIPAGENT_OFFLINE_MODE=false
```

## Verification

```bash
pytest
docker compose exec postgres psql -U shipagent -d shipagent_db -c "\dt"
docker compose exec postgres psql -U shipagent -d shipagent_db -c "SELECT COUNT(*) FROM knowledge_chunks;"
docker compose exec redis redis-cli ping
```

If another local PostgreSQL is already listening on `5432`, this Compose file publishes ShipAgent Postgres on host port `55432` while containers still use `postgres:5432`.
