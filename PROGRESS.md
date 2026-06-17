# ShipAgent Progress Report

Last verified: 2026-06-17

## Short Answer

The project is complete as a local, Docker-verified, offline-safe agentic AI implementation.

It is not fully complete as a live paid-service production demo because live Claude/OpenAI/Twilio calls are intentionally disabled with `SHIPAGENT_OFFLINE_MODE=true`, and Twilio credentials/WhatsApp sandbox delivery are still placeholders or unverified.

## Repository

- GitHub repo: https://github.com/Achintya17408/shiprocket-shipagent
- Visibility: public
- Local branch: `main`
- Remote: `origin/main`
- Latest pushed commit at verification time: `aa43db2 test: cover real api paths without network spend`

## What Is Complete

- Required repository structure exists.
- FastAPI backend exists.
- LangGraph workflow exists in `agent/graph.py`.
- LangGraph nodes exist in `agent/nodes.py`.
- LangChain tools exist in `agent/tools.py`.
- Claude/OpenAI model routing exists in `agent/llm_router.py`.
- Prompt templates exist in `agent/prompts.py`.
- PostgreSQL + pgvector schema exists in `db/schema.sql`.
- RAG service exists in `services/rag_service.py`.
- Twilio alert service exists in `services/alert_service.py`.
- RTO predictor exists in `services/rto_predictor.py`.
- Redis-backed polling support exists in `services/order_poller.py`.
- Knowledge seeding exists in `scripts/seed_knowledge.py`.
- Test order seeding exists in `tests/seed_orders.py`.
- Unit tests exist and pass.
- Docker Compose exists and starts PostgreSQL + Redis.
- Dockerfile exists and uses Python 3.11 slim with `gcc` and `libpq-dev`.
- `.env.example` exists.
- `.env` exists locally and is gitignored.
- README exists and includes architecture and usage.
- Interview prep exists in `INTERVIEW_PREP.md`.

## Verification Evidence

### Tests

Command:

```bash
.venv/bin/pytest -q
```

Result:

```text
8 passed in 1.62s
```

### Docker Services

Command:

```bash
docker compose ps
```

Result:

```text
shipagent-postgres-1   pgvector/pgvector:pg17   Up   0.0.0.0:55432->5432/tcp
shipagent-redis-1      redis:7-alpine           Up   0.0.0.0:6379->6379/tcp
```

Note: host port `55432` is used because this machine already has another PostgreSQL listening on `5432`. Containers still use `postgres:5432`.

### Database Tables

Command:

```bash
docker compose exec postgres psql -U shipagent -d shipagent_db -c "\dt"
```

Verified tables:

```text
agent_decisions
alerts
knowledge_chunks
orders
```

### pgvector

Command:

```bash
docker compose exec postgres psql -U shipagent -d shipagent_db -c "SELECT extname FROM pg_extension WHERE extname='vector';"
```

Result:

```text
vector
```

### Seed Data

Command:

```bash
docker compose exec postgres psql -U shipagent -d shipagent_db -c "SELECT COUNT(*) AS knowledge_count FROM knowledge_chunks; SELECT COUNT(*) AS order_count FROM orders;"
```

Result:

```text
knowledge_count = 8
order_count = 4
```

### Redis

Command:

```bash
docker compose exec redis redis-cli ping
```

Result:

```text
PONG
```

### API Smoke Test

The API was verified on port `8001` because port `8000` was occupied by another local app.

Command:

```bash
curl http://127.0.0.1:8001/health
```

Result:

```json
{"status":"ok"}
```

### Agent Decisions

Command:

```bash
curl http://127.0.0.1:8001/agent/decisions
```

Verified:

- `CLASSIFICATION_HIGH_RTO_RISK` used `claude-haiku-4-5-20251001`
- `ALERT_HIGH_RTO_RISK` used `claude-sonnet-4-6`
- Final decision row exists for `HIGH_RTO_RISK`

### Orders Endpoint

Command:

```bash
curl http://127.0.0.1:8001/orders/
```

Verified:

- Returns seeded orders.
- `ORD-002` is flagged as `rto_risk_flagged`.

### Alerts Endpoint

Command:

```bash
curl http://127.0.0.1:8001/alerts/
```

Verified:

- Returns a WhatsApp alert record for `ORD-002`.
- Status is `sent` in offline demo mode.

## Real API Key Status

Anthropic and OpenAI keys are configured locally in `.env`.

They are not committed to git. `.env` is ignored by `.gitignore`.

Current safety setting:

```env
SHIPAGENT_OFFLINE_MODE=true
```

This prevents accidental credit usage. Tests also include mocked real-mode checks that force `SHIPAGENT_OFFLINE_MODE=false` but replace the Anthropic/OpenAI clients with fakes, proving the real code paths are wired without spending credits.

## Definition Of Done Status

| Requirement | Status | Notes |
|---|---:|---|
| `docker compose up postgres redis -d` starts | Done | Verified running |
| PostgreSQL tables exist | Done | 4 required tables verified |
| pgvector extension loaded | Done | `vector` extension verified |
| `scripts/seed_knowledge.py` seeds 8 chunks | Done | Count verified as 8 |
| `tests/seed_orders.py` seeds 4 orders | Done | Count verified as 4 |
| `GET /health` returns ok | Done | Verified on `8001` |
| `POST /agent/run` returns correct anomaly | Done | Previously verified for `ORD-002` high RTO risk |
| WhatsApp alert received on merchant number | Not fully done | Offline alert record verified; real Twilio delivery not verified |
| `/agent/decisions` shows Haiku and Sonnet | Done | Verified |
| `/orders/` and `/alerts/` return data | Done | Verified |
| `agent_decisions` has rows after run | Done | Count verified as 3 |
| `llm_router.py` documents model choices | Done | Present |
| Secrets in `.env`, not committed | Done | `.env` gitignored |
| Repository pushed to GitHub | Done | Public GitHub repo exists |
| README shows architecture diagram | Done | ASCII architecture exists |
| README has screenshots | Not done | Screenshots were not captured/committed |
| Live Claude/OpenAI inference | Intentionally not done | Disabled to avoid free-tier credit spend |
| Live Twilio WhatsApp delivery | Not done | Twilio credentials/merchant number are placeholders or unverified |

## Final Status

Use this wording:

> The project is complete and verified as a local Docker-based agentic RAG system. The only incomplete pieces from the original production-style checklist are live Twilio WhatsApp delivery, real paid LLM/embedding calls, and screenshots in README. Those are intentionally left out or disabled to avoid exposing secrets and spending free-tier credits.

## Demo Command Sequence

```bash
docker compose up postgres redis -d
source .venv/bin/activate
python scripts/seed_knowledge.py
python tests/seed_orders.py
uvicorn api.main:app --host 127.0.0.1 --port 8001
```

Then in another terminal:

```bash
curl http://127.0.0.1:8001/health
curl -X POST http://127.0.0.1:8001/agent/run
curl http://127.0.0.1:8001/agent/decisions
curl http://127.0.0.1:8001/orders/
curl http://127.0.0.1:8001/alerts/
```
