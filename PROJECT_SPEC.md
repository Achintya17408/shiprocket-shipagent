# ShipAgent — Agentic Order Intelligence System

> **Codex / Agent Instruction:** This is a complete agentic AI system with RAG. All tool setup is in Sprint 1 — complete every signup and installation step before writing any code. Follow every story in exact order. The system uses LangGraph for agent orchestration, Claude API for LLM inference, FastAPI for the backend, PostgreSQL + pgvector for state persistence and RAG retrieval. Do not substitute any tool. Implement completely in one pass.

---

## Exact Stack

| Layer | Tool | Purpose |
|---|---|---|
| Agent orchestration | LangGraph | State machine, tool routing, multi-step reasoning |
| LLM — classification | Claude Haiku (claude-haiku-4-5-20251001) | Fast, cheap anomaly classification |
| LLM — summaries | Claude Sonnet (claude-sonnet-4-6) | Detailed alert summaries for merchants |
| LLM — fallback | OpenAI GPT-4o-mini | Fallback when Anthropic rate-limited |
| Embeddings | OpenAI text-embedding-3-small | Converts courier/case text to vectors for RAG |
| Agent framework | LangChain | Tool definitions, prompt templates |
| Backend API | FastAPI | Webhook receiver + dashboard endpoints |
| Database | PostgreSQL + pgvector | Order state, agent decisions, alert history, RAG knowledge base |
| Alerting | Twilio (WhatsApp) | Merchant alerts for critical issues |
| Task queue | Redis | Background task scheduling |
| Containerisation | Docker + Docker Compose | Single-command startup |
| Language | Python 3.11 | All backend code |

---

## Repository Structure

```
shiprocket-shipagent/
├── agent/
│   ├── graph.py               # LangGraph state machine definition
│   ├── nodes.py               # individual agent node functions
│   ├── tools.py               # LangChain tool definitions
│   ├── llm_router.py          # model selection logic (Haiku vs Sonnet vs GPT)
│   └── prompts.py             # all prompt templates
├── api/
│   ├── main.py                # FastAPI app
│   ├── routes/
│   │   ├── orders.py          # order webhook + status endpoints
│   │   ├── alerts.py          # alert history endpoint
│   │   └── agent.py           # agent trigger + decision log endpoint
│   └── models.py              # Pydantic models
├── db/
│   ├── schema.sql             # PostgreSQL + pgvector table definitions
│   └── connection.py          # sync pg connection pool
├── services/
│   ├── order_poller.py        # polls order pipeline on schedule
│   ├── alert_service.py       # Twilio WhatsApp sender
│   ├── rto_predictor.py       # rule-based + LLM RTO risk scorer
│   └── rag_service.py         # embedding + pgvector retrieval for RAG
├── scripts/
│   └── seed_knowledge.py      # embeds courier policies into pgvector
├── tests/
│   ├── test_agent.py
│   ├── test_tools.py
│   └── seed_orders.py         # seeds test orders into PostgreSQL
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── requirements.txt
└── README.md
```

---

## Sprint 1 — All Tool Setup and Account Creation

### Story 1.1 — Python environment
**Tasks:**
1. Download Anaconda from `anaconda.com/download` → install → open terminal
2. `conda create -n shipagent python=3.11 -y && conda activate shipagent`
3. Create `requirements.txt`:
```
fastapi
uvicorn[standard]
langchain
langchain-anthropic
langchain-openai
langgraph
anthropic
openai
psycopg2-binary
asyncpg
sqlalchemy
pgvector
redis
celery
twilio
python-dotenv
pydantic
httpx
pytest
pytest-asyncio
```
4. `pip install -r requirements.txt`
5. Verify: `python -c "import langchain, langgraph, anthropic, openai, fastapi, twilio, pgvector; print('ALL OK')"`

### Story 1.2 — Docker Desktop installation
**Tasks:**
1. Go to `docker.com/products/docker-desktop` → download for your OS → install
2. Start Docker Desktop
3. Verify: `docker --version` and `docker compose version` — both must return versions
4. Docker will run PostgreSQL (with pgvector) and Redis — no separate installation needed

### Story 1.3 — Anthropic API key
**Tasks:**
1. Go to `console.anthropic.com` → sign up with email → verify email
2. Go to API Keys → Create Key → name: `shipagent-dev`
3. Copy the key (starts with `sk-ant-...`) — you see it only once
4. Store in `.env` (created in Story 1.7)
5. Free tier: $5 credit on signup, sufficient for development and testing

### Story 1.4 — OpenAI API key (fallback LLM + embeddings)
**Tasks:**
1. Go to `platform.openai.com` → sign up → verify
2. Go to API Keys → Create new secret key → name: `shipagent-fallback`
3. Copy key (starts with `sk-...`)
4. Free tier: $5 credit on new accounts — sufficient for testing
5. Store in `.env`
6. Note: this key is used for BOTH GPT-4o-mini fallback AND text-embedding-3-small for RAG

### Story 1.5 — Twilio account (WhatsApp alerts)
**Tasks:**
1. Go to `twilio.com` → click "Sign up for free" → fill details → verify phone
2. Free trial: $15.50 credit — sufficient for testing hundreds of WhatsApp messages
3. From Twilio Console: copy `Account SID` and `Auth Token`
4. Enable WhatsApp Sandbox:
   - Go to Messaging → Try it out → Send a WhatsApp message
   - Follow instructions: send "join [word]-[word]" from your WhatsApp to the Twilio sandbox number
   - This activates the sandbox — your phone can now receive agent alerts
5. Note the sandbox number (format: `whatsapp:+14155238886`) and your number
6. Store in `.env`

### Story 1.6 — GitHub repository
**Tasks:**
1. `github.com` → New repository → name: `shiprocket-shipagent` → Public → Create
2. In project folder:
```bash
git init
git remote add origin https://github.com/YOUR_USERNAME/shiprocket-shipagent.git
```
3. Create `.gitignore`:
```
.env
__pycache__/
*.pyc
.DS_Store
*.egg-info/
dist/
.pytest_cache/
```
4. `git add .gitignore requirements.txt && git commit -m "initial" && git push -u origin main`

### Story 1.7 — Create .env file
**Tasks:**
1. Create `.env.example`:
```env
# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# OpenAI (fallback LLM + embeddings for RAG)
OPENAI_API_KEY=sk-...

# Twilio
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
MERCHANT_WHATSAPP_TO=whatsapp:+91XXXXXXXXXX

# PostgreSQL
DATABASE_URL=postgresql://shipagent:shipagent123@localhost:5432/shipagent_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Agent config
POLL_INTERVAL_SECONDS=300
RTO_RISK_THRESHOLD=0.7
STUCK_ORDER_HOURS=24

# RAG config
EMBEDDING_MODEL=text-embedding-3-small
RAG_TOP_K=3
```
2. Copy: `cp .env.example .env`
3. Fill all values from the accounts created above
4. `.env` is in `.gitignore` — confirm it is NOT committed

---

## Sprint 2 — Infrastructure: PostgreSQL (with pgvector) and Redis via Docker

### Story 2.1 — Docker Compose setup
**Tasks:**
1. Create `docker-compose.yml`:

> **Critical:** Use `pgvector/pgvector:pg17` image — NOT `postgres:17`. The standard postgres image does not include the pgvector extension. This single change is what enables semantic vector search inside PostgreSQL without a separate vector database.

```yaml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg17
    environment:
      POSTGRES_USER: shipagent
      POSTGRES_PASSWORD: shipagent123
      POSTGRES_DB: shipagent_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./db/schema.sql:/docker-entrypoint-initdb.d/schema.sql

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://shipagent:shipagent123@postgres:5432/shipagent_db
      - REDIS_URL=redis://redis:6379/0
    env_file: .env
    depends_on:
      - postgres
      - redis
    command: uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

volumes:
  postgres_data:
```

2. Create `Dockerfile`:

> **Critical:** Use `python:3.11-slim` with `gcc` and `libpq-dev` build tools — the `pgvector` Python package requires C compilation. Without these, `pip install pgvector` will fail silently or error during build.

```dockerfile
FROM python:3.11-slim
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Story 2.2 — Database schema
**Tasks:**
1. Create `db/schema.sql`:
```sql
-- Enable pgvector extension FIRST — must be before any vector column
CREATE EXTENSION IF NOT EXISTS vector;

-- Orders table (simulates Shiprocket order pipeline)
CREATE TABLE IF NOT EXISTS orders (
    id              SERIAL PRIMARY KEY,
    order_id        VARCHAR(50) UNIQUE NOT NULL,
    merchant_id     VARCHAR(50) NOT NULL,
    status          VARCHAR(30) NOT NULL,
    courier         VARCHAR(50),
    awb             VARCHAR(50),
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW(),
    pickup_city     VARCHAR(100),
    delivery_city   VARCHAR(100),
    amount          DECIMAL(10,2),
    payment_method  VARCHAR(20),
    attempts        INTEGER DEFAULT 0,
    rto_risk_score  DECIMAL(4,3) DEFAULT 0.0
);

-- Agent decision log
CREATE TABLE IF NOT EXISTS agent_decisions (
    id              SERIAL PRIMARY KEY,
    order_id        VARCHAR(50),
    decision_type   VARCHAR(50) NOT NULL,
    input_summary   TEXT,
    reasoning       TEXT,
    action_taken    VARCHAR(100),
    llm_used        VARCHAR(50),
    latency_ms      INTEGER,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Alert history
CREATE TABLE IF NOT EXISTS alerts (
    id              SERIAL PRIMARY KEY,
    order_id        VARCHAR(50),
    alert_type      VARCHAR(50) NOT NULL,
    channel         VARCHAR(20) NOT NULL,
    recipient       VARCHAR(100),
    message         TEXT,
    sent_at         TIMESTAMP DEFAULT NOW(),
    status          VARCHAR(20) DEFAULT 'sent'
);

-- RAG knowledge base — courier policies and historical case resolutions
CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id          SERIAL PRIMARY KEY,
    source      VARCHAR(100),
    content     TEXT,
    embedding   vector(1536),
    metadata    JSONB,
    created_at  TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_merchant ON orders(merchant_id);
CREATE INDEX IF NOT EXISTS idx_decisions_order ON agent_decisions(order_id);
CREATE INDEX IF NOT EXISTS idx_alerts_order ON alerts(order_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_embedding ON knowledge_chunks
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

### Story 2.3 — Start infrastructure and verify
**Tasks:**
1. `docker compose up postgres redis -d`
2. Wait 5 seconds for postgres to initialise, then verify tables exist:
```bash
docker compose exec postgres psql -U shipagent -d shipagent_db -c "\dt"
```
3. Expected output: `orders`, `agent_decisions`, `alerts`, `knowledge_chunks` all listed
4. Verify pgvector extension loaded:
```bash
docker compose exec postgres psql -U shipagent -d shipagent_db -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```
5. Expected: one row with `extname = vector`
6. Verify Redis:
```bash
docker compose exec redis redis-cli ping
```
7. Expected: `PONG`

---

## Sprint 3 — LLM Router: Model Selection Logic

### Story 3.1 — LLM router
**Tasks:**
1. Create `agent/llm_router.py`:
```python
"""
LLM Router — decides which model to use per task type.

Decision logic:
- Haiku  → fast classification tasks (<200ms latency target, <$0.001/call)
- Sonnet → complex reasoning, multi-step summaries, merchant-facing output
- GPT-4o-mini → fallback when Anthropic is rate-limited, or for comparison
"""

import os
from anthropic import Anthropic
from openai import OpenAI
from dotenv import load_dotenv
import time

load_dotenv()

anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
openai_client    = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

HAIKU    = "claude-haiku-4-5-20251001"
SONNET   = "claude-sonnet-4-6"
GPT_MINI = "gpt-4o-mini"


def classify_with_haiku(prompt: str) -> dict:
    """
    Use Haiku for: anomaly classification, risk scoring, intent detection.
    Reason: Sub-200ms latency, $0.00025/1K tokens — cheap enough to run on every order.
    """
    start = time.time()
    try:
        response = anthropic_client.messages.create(
            model=HAIKU,
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        return {
            "result": response.content[0].text,
            "model": HAIKU,
            "latency_ms": int((time.time() - start) * 1000),
            "success": True
        }
    except Exception as e:
        return fallback_to_gpt(prompt, error=str(e))


def summarise_with_sonnet(prompt: str) -> dict:
    """
    Use Sonnet for: merchant alert summaries, resolution recommendations,
    multi-step reasoning about order anomalies.
    Reason: Better reasoning than Haiku, merchant-facing output must be clear.
    Only called for alerts — not every order scan.
    """
    start = time.time()
    try:
        response = anthropic_client.messages.create(
            model=SONNET,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        return {
            "result": response.content[0].text,
            "model": SONNET,
            "latency_ms": int((time.time() - start) * 1000),
            "success": True
        }
    except Exception as e:
        return fallback_to_gpt(prompt, error=str(e))


def fallback_to_gpt(prompt: str, error: str = "") -> dict:
    """
    Fallback to GPT-4o-mini when Anthropic is rate-limited or unavailable.
    Reason: Operational reliability — single-LLM dependency is a production risk.
    """
    start = time.time()
    response = openai_client.chat.completions.create(
        model=GPT_MINI,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300
    )
    return {
        "result": response.choices[0].message.content,
        "model": GPT_MINI,
        "latency_ms": int((time.time() - start) * 1000),
        "success": True,
        "fallback_reason": error
    }
```

---

## Sprint 4 — RAG Service and Knowledge Base

### Story 4.1 — RAG service
**Tasks:**
1. Create `services/rag_service.py`:
```python
"""
RAG Service — retrieves relevant context before LLM classification.

Uses pgvector on the existing PostgreSQL instance — no separate vector DB needed.
Embeds courier SLA policies and historical case resolutions using
text-embedding-3-small (1536 dims), then retrieves top-k semantically
similar chunks via cosine similarity before Haiku classification.

Why RAG here: courier policies and historical cases are unstructured text.
SQL cannot semantically search them. pgvector can.
"""

import os
from openai import OpenAI
from db.connection import get_db_connection
from dotenv import load_dotenv

load_dotenv()

client          = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
RAG_TOP_K       = int(os.getenv("RAG_TOP_K", 3))


def get_embedding(text: str) -> list:
    """Convert text to 1536-dim vector using OpenAI embeddings."""
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )
    return response.data[0].embedding


def retrieve_relevant_context(query: str, top_k: int = RAG_TOP_K) -> str:
    """
    Retrieve top-k semantically similar chunks from knowledge_chunks table.
    Called before Haiku classification to enrich the prompt with
    courier SLA context and historical resolution patterns.
    """
    embedding = get_embedding(query)
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT content, source,
                       1 - (embedding <=> %s::vector) AS similarity
                FROM knowledge_chunks
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """, (embedding, embedding, top_k))
            rows = cur.fetchall()
    if not rows:
        return "No relevant context found in knowledge base."
    return "\n\n".join([
        f"[{r[1]}] (similarity: {r[2]:.2f}): {r[0]}" for r in rows
    ])


def add_knowledge_chunk(source: str, content: str, metadata: dict = None) -> None:
    """Embed and store a knowledge chunk into the pgvector knowledge base."""
    if metadata is None:
        metadata = {}
    embedding = get_embedding(content)
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO knowledge_chunks (source, content, embedding, metadata)
                VALUES (%s, %s, %s::vector, %s)
            """, (source, content, embedding, str(metadata)))
            conn.commit()
```

### Story 4.2 — Seed knowledge base
**Tasks:**
1. Create `scripts/seed_knowledge.py`:
```python
"""
Seed the pgvector knowledge base with courier SLA policies and historical cases.
Run once before the first agent run: python scripts/seed_knowledge.py
Each chunk is embedded via text-embedding-3-small and stored as a
1536-dim vector in the knowledge_chunks table.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.rag_service import add_knowledge_chunk

COURIER_POLICIES = [
    {
        "source": "courier_policy",
        "content": (
            "Delhivery SLA for tier-3 cities (Patna, Varanasi, Agra): 7 business days. "
            "RTO rate in tier-3 zones averages 34%. COD orders above Rs.2000 have 2x higher RTO probability. "
            "Second delivery attempt success rate: 52%. Third attempt: 31%."
        ),
    },
    {
        "source": "courier_policy",
        "content": (
            "BlueDart SLA for metro cities (Mumbai, Delhi, Bangalore, Chennai): 2-3 business days. "
            "RTO rate in metros averages 8%. Prepaid orders rarely RTO. "
            "Stuck shipments in BlueDart metro hubs are typically resolved within 6 hours on escalation."
        ),
    },
    {
        "source": "courier_policy",
        "content": (
            "DTDC SLA for tier-2 cities (Pune, Jaipur, Lucknow, Indore): 4-5 business days. "
            "Second delivery attempt success rate: 61%. Third attempt: 38%. "
            "COD above Rs.1500 in tier-2 cities has elevated RTO risk of 28%."
        ),
    },
    {
        "source": "courier_policy",
        "content": (
            "Ekart SLA for metro and tier-2 cities: 3-4 business days. "
            "Strong last-mile network in South India. RTO rate averages 11%. "
            "Prepaid orders in metro cities: RTO rate under 5%."
        ),
    },
]

HISTORICAL_CASES = [
    {
        "source": "past_case",
        "content": (
            "Order stuck in_transit via Delhivery in Patna for 32 hours. COD Rs.2200. "
            "Resolution: courier retry triggered via merchant portal. Delivered on attempt 2. "
            "RTO avoided. Key action: early retry within 36 hours of no update prevents most RTOs."
        ),
    },
    {
        "source": "past_case",
        "content": (
            "Order out_for_delivery via Ekart in Delhi, 2 failed attempts. Prepaid Rs.1200. "
            "Resolution: merchant contacted customer directly, rescheduled delivery. "
            "Delivered on attempt 3. Customer was unreachable — address pin needed update."
        ),
    },
    {
        "source": "past_case",
        "content": (
            "SLA breach detected for BlueDart shipment in Mumbai after 4 days. Prepaid Rs.800. "
            "Resolution: escalated to courier account manager, expedited same-day delivery. "
            "Merchant received compensation credit for SLA miss."
        ),
    },
    {
        "source": "past_case",
        "content": (
            "High RTO risk order via Delhivery in Varanasi. COD Rs.3100, 1 failed attempt. "
            "Agent flagged RTO risk score 0.82. Resolution: merchant called customer proactively. "
            "Customer confirmed delivery, order delivered next day. Proactive call reduces COD RTO by 40%."
        ),
    },
]

if __name__ == "__main__":
    print("Seeding courier policies into pgvector knowledge base...")
    for item in COURIER_POLICIES:
        add_knowledge_chunk(**item)
        print(f"  [OK] {item['content'][:70]}...")

    print("\nSeeding historical case resolutions...")
    for item in HISTORICAL_CASES:
        add_knowledge_chunk(**item)
        print(f"  [OK] {item['content'][:70]}...")

    print("\nKnowledge base seeded successfully. 8 chunks embedded and stored.")
```
2. Run: `python scripts/seed_knowledge.py`
3. Verify: `docker compose exec postgres psql -U shipagent -d shipagent_db -c "SELECT COUNT(*) FROM knowledge_chunks;"`
4. Expected: count = 8

---

## Sprint 5 — Agent Tools

### Story 5.1 — Define LangChain tools
**Tasks:**
1. Create `agent/tools.py`:
```python
from langchain.tools import tool
from db.connection import get_db_connection
from services.alert_service import send_whatsapp_alert
import json


@tool
def get_order_status(order_id: str) -> str:
    """
    Fetch the current status of an order from the database.
    Use this when the agent needs to verify order state before taking action.
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT order_id, status, courier, awb, attempts,
                          rto_risk_score, updated_at
                   FROM orders WHERE order_id = %s""",
                (order_id,)
            )
            row = cur.fetchone()
            if not row:
                return f"Order {order_id} not found"
            cols = ["order_id", "status", "courier", "awb", "attempts",
                    "rto_risk_score", "updated_at"]
            return json.dumps(dict(zip(cols, row)), default=str)


@tool
def flag_rto_risk(order_id: str, risk_score: float, reason: str) -> str:
    """
    Flag an order as high RTO risk in the database.
    Use when rto_risk_score > 0.7 and reason is identified.
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE orders SET rto_risk_score = %s, status = 'rto_risk_flagged'
                   WHERE order_id = %s""",
                (risk_score, order_id)
            )
            conn.commit()
    return f"Order {order_id} flagged as RTO risk (score: {risk_score}). Reason: {reason}"


@tool
def send_merchant_alert(order_id: str, alert_type: str, message: str) -> str:
    """
    Send a WhatsApp alert to the merchant about a critical order issue.
    Use for: stuck orders, RTO risk, SLA breach predictions.
    Do NOT use for routine status updates.
    """
    result = send_whatsapp_alert(message)
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO alerts (order_id, alert_type, channel, message, status)
                   VALUES (%s, %s, 'whatsapp', %s, %s)""",
                (order_id, alert_type, message, "sent" if result else "failed")
            )
            conn.commit()
    return f"Alert sent for order {order_id}: {alert_type}"


@tool
def escalate_to_human(order_id: str, reason: str, priority: str) -> str:
    """
    Log an escalation for human review when the agent cannot resolve autonomously.
    Use when: courier unresponsive, payment dispute, fraud suspicion.
    Priority must be: 'low', 'medium', 'high', 'critical'
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO agent_decisions
                   (order_id, decision_type, reasoning, action_taken, llm_used)
                   VALUES (%s, 'escalation', %s, %s, 'system')""",
                (order_id, reason, f"Escalated to human — priority: {priority}")
            )
            conn.commit()
    return f"Order {order_id} escalated. Priority: {priority}. Reason: {reason}"


@tool
def log_agent_decision(order_id: str, decision_type: str, reasoning: str,
                       action_taken: str, llm_used: str, latency_ms: int) -> str:
    """
    Log every agent decision to the audit trail in PostgreSQL.
    Must be called after every decision — auditability is non-negotiable.
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO agent_decisions
                   (order_id, decision_type, reasoning, action_taken, llm_used, latency_ms)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (order_id, decision_type, reasoning, action_taken, llm_used, latency_ms)
            )
            conn.commit()
    return "Decision logged"


TOOLS = [get_order_status, flag_rto_risk, send_merchant_alert,
         escalate_to_human, log_agent_decision]
```

---

## Sprint 6 — Agent Prompts

### Story 6.1 — Prompt templates
**Tasks:**
1. Create `agent/prompts.py`:
```python
ANOMALY_CLASSIFICATION_PROMPT = """
You are an order anomaly classifier for an e-commerce logistics platform.
Analyse this order and classify the issue type.

Order data:
{order_data}

Relevant context retrieved from courier policies and historical case resolutions:
{retrieved_context}

Use the retrieved context to inform your classification — for example, if the
courier has a known high RTO rate in this city, weight that appropriately.

Classify as exactly one of:
- STUCK_ORDER: order not updated for > 24 hours
- HIGH_RTO_RISK: delivery likely to fail and return (COD + remote pin code + previous attempts > 1)
- SLA_BREACH: expected delivery date passed, order not delivered
- PAYMENT_ANOMALY: COD amount mismatch or suspicious pattern
- NORMAL: no issue detected

Respond in JSON only:
{{"issue_type": "...", "confidence": 0.0-1.0, "reason": "one sentence referencing courier context if relevant"}}
"""

MERCHANT_ALERT_PROMPT = """
You are writing a WhatsApp alert for an SMB merchant using Shiprocket.
The merchant is non-technical. Be direct, helpful, and specific.
Keep it under 150 words.

Issue: {issue_type}
Order ID: {order_id}
Details: {details}

Write the alert message. Start with the issue, then what is happening,
then what the merchant should do (if anything).
"""

RTO_RISK_ASSESSMENT_PROMPT = """
Assess the RTO (Return to Origin) risk for this shipment.

Order details:
- Payment method: {payment_method}
- Delivery city: {delivery_city}
- Delivery attempts: {attempts}
- Order amount: {amount}
- Days since last update: {days_stale}

RTO risk factors:
- COD orders have 3x higher RTO rate than prepaid
- Delivery attempts > 1 strongly predicts RTO
- Remote/tier-3 cities have higher RTO rates
- High-value COD orders (> Rs.2000) have elevated risk

Return a JSON:
{{"rto_risk_score": 0.0-1.0, "primary_risk_factor": "...", "recommendation": "..."}}
"""
```

---

## Sprint 7 — LangGraph Agent State Machine

### Story 7.1 — Agent graph definition
**Tasks:**
1. Create `agent/graph.py`:
```python
"""
LangGraph state machine for ShipAgent.
Each node is a discrete step. Edges are conditional routing decisions.

Graph flow:
poll_orders → classify_anomaly → route_anomaly → [handler] → send_alert → log_decision → END
                                                    ↓
                                             NORMAL → log_decision → END
"""

from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Optional
from agent.nodes import (
    poll_orders_node,
    classify_anomaly_node,
    route_anomaly_node,
    resolve_stuck_order_node,
    assess_rto_risk_node,
    send_alert_node,
    escalate_node,
    log_decision_node
)


class AgentState(TypedDict):
    orders_to_process: List[dict]
    current_order:     Optional[dict]
    classification:    Optional[dict]
    rto_assessment:    Optional[dict]
    resolution_result: Optional[str]
    alert_sent:        bool
    llm_used:          str
    latency_ms:        int
    decisions:         List[dict]


def build_agent_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("poll_orders",      poll_orders_node)
    graph.add_node("classify_anomaly", classify_anomaly_node)
    graph.add_node("route_anomaly",    route_anomaly_node)
    graph.add_node("resolve_stuck",    resolve_stuck_order_node)
    graph.add_node("assess_rto",       assess_rto_risk_node)
    graph.add_node("send_alert",       send_alert_node)
    graph.add_node("escalate",         escalate_node)
    graph.add_node("log_decision",     log_decision_node)

    graph.set_entry_point("poll_orders")
    graph.add_edge("poll_orders",      "classify_anomaly")
    graph.add_edge("classify_anomaly", "route_anomaly")

    graph.add_conditional_edges(
        "route_anomaly",
        lambda state: state["classification"]["issue_type"],
        {
            "STUCK_ORDER":     "resolve_stuck",
            "HIGH_RTO_RISK":   "assess_rto",
            "SLA_BREACH":      "send_alert",
            "PAYMENT_ANOMALY": "escalate",
            "NORMAL":          "log_decision",
        }
    )

    graph.add_edge("resolve_stuck", "send_alert")
    graph.add_edge("assess_rto",    "send_alert")
    graph.add_edge("send_alert",    "log_decision")
    graph.add_edge("escalate",      "log_decision")
    graph.add_edge("log_decision",  END)

    return graph.compile()


agent_graph = build_agent_graph()
```

---

## Sprint 8 — Agent Node Implementations

### Story 8.1 — All node functions
**Tasks:**
1. Create `agent/nodes.py`:
```python
from agent.llm_router import classify_with_haiku, summarise_with_sonnet
from agent.prompts import (ANOMALY_CLASSIFICATION_PROMPT,
                            MERCHANT_ALERT_PROMPT,
                            RTO_RISK_ASSESSMENT_PROMPT)
from agent.tools import (flag_rto_risk, send_merchant_alert,
                          escalate_to_human, log_agent_decision)
from services.rag_service import retrieve_relevant_context
from db.connection import get_db_connection
import json
from datetime import datetime, timedelta
import os

STUCK_HOURS   = int(os.getenv("STUCK_ORDER_HOURS", 24))
RTO_THRESHOLD = float(os.getenv("RTO_RISK_THRESHOLD", 0.7))


def poll_orders_node(state: dict) -> dict:
    """Fetch orders that need attention from PostgreSQL."""
    stuck_cutoff = datetime.now() - timedelta(hours=STUCK_HOURS)
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT order_id, merchant_id, status, courier, awb, attempts,
                       rto_risk_score, payment_method, delivery_city, amount,
                       updated_at, created_at
                FROM orders
                WHERE (updated_at < %s AND status NOT IN ('delivered','cancelled','rto_complete'))
                   OR (rto_risk_score > %s AND status != 'rto_risk_flagged')
                LIMIT 50
            """, (stuck_cutoff, RTO_THRESHOLD))
            rows = cur.fetchall()
            cols = ["order_id", "merchant_id", "status", "courier", "awb", "attempts",
                    "rto_risk_score", "payment_method", "delivery_city", "amount",
                    "updated_at", "created_at"]
            orders = [dict(zip(cols, r)) for r in rows]
    state["orders_to_process"] = orders
    state["current_order"]     = orders[0] if orders else None
    print(f"[poll_orders] Found {len(orders)} orders needing attention")
    return state


def classify_anomaly_node(state: dict) -> dict:
    """
    Use Claude Haiku to classify the anomaly type.
    RAG context (courier policies + historical cases) is retrieved via
    pgvector cosine similarity and injected into the prompt before classification.
    """
    order = state.get("current_order")
    if not order:
        state["classification"] = {"issue_type": "NORMAL", "confidence": 1.0, "reason": "no orders"}
        return state

    # Build semantic query from order fields and retrieve relevant context
    rag_query = (
        f"{order.get('courier', '')} {order.get('delivery_city', '')} "
        f"{order.get('payment_method', '')} attempts:{order.get('attempts', 0)}"
    )
    retrieved_context = retrieve_relevant_context(rag_query)

    prompt = ANOMALY_CLASSIFICATION_PROMPT.format(
        order_data=json.dumps(order, default=str),
        retrieved_context=retrieved_context
    )
    result = classify_with_haiku(prompt)

    try:
        classification = json.loads(result["result"])
    except json.JSONDecodeError:
        classification = {"issue_type": "NORMAL", "confidence": 0.5, "reason": "parse error"}

    state["classification"] = classification
    state["llm_used"]       = result["model"]
    state["latency_ms"]     = result["latency_ms"]
    print(f"[classify] Order {order['order_id']}: {classification['issue_type']} "
          f"({classification['confidence']:.2f})")
    return state


def route_anomaly_node(state: dict) -> dict:
    """Routing node — no LLM call needed. Pure conditional logic."""
    issue = state["classification"]["issue_type"]
    print(f"[route] Routing to handler: {issue}")
    return state


def resolve_stuck_order_node(state: dict) -> dict:
    """Handle stuck orders — log and prepare alert."""
    order = state["current_order"]
    state["resolution_result"] = (
        f"Stuck order detected: {order['order_id']} "
        f"last updated {order['updated_at']}"
    )
    return state


def assess_rto_risk_node(state: dict) -> dict:
    """Use Claude Sonnet for detailed RTO risk assessment."""
    order      = state["current_order"]
    updated_at = order.get("updated_at")
    days_stale = (datetime.now() - updated_at).days if updated_at else 0

    prompt = RTO_RISK_ASSESSMENT_PROMPT.format(
        payment_method=order.get("payment_method", "unknown"),
        delivery_city=order.get("delivery_city", "unknown"),
        attempts=order.get("attempts", 0),
        amount=order.get("amount", 0),
        days_stale=days_stale
    )
    result = summarise_with_sonnet(prompt)

    try:
        assessment = json.loads(result["result"])
    except json.JSONDecodeError:
        assessment = {
            "rto_risk_score": 0.5,
            "primary_risk_factor": "unknown",
            "recommendation": "manual review"
        }

    state["rto_assessment"] = assessment
    state["llm_used"]       = result["model"]

    if assessment["rto_risk_score"] >= RTO_THRESHOLD:
        flag_rto_risk.invoke({
            "order_id":   order["order_id"],
            "risk_score": assessment["rto_risk_score"],
            "reason":     assessment["primary_risk_factor"]
        })
    return state


def send_alert_node(state: dict) -> dict:
    """Use Claude Sonnet to draft a merchant-friendly WhatsApp alert."""
    order      = state["current_order"]
    issue_type = state["classification"]["issue_type"]
    details    = state.get("rto_assessment") or state.get("resolution_result") or {}

    prompt = MERCHANT_ALERT_PROMPT.format(
        issue_type=issue_type,
        order_id=order["order_id"],
        details=json.dumps(details, default=str)
    )
    result  = summarise_with_sonnet(prompt)
    message = result["result"]

    send_merchant_alert.invoke({
        "order_id":   order["order_id"],
        "alert_type": issue_type,
        "message":    message
    })
    state["alert_sent"] = True
    state["llm_used"]   = result["model"]
    return state


def escalate_node(state: dict) -> dict:
    """Escalate unresolvable issues to human review."""
    order  = state["current_order"]
    reason = state["classification"]["reason"]
    escalate_to_human.invoke({
        "order_id": order["order_id"],
        "reason":   reason,
        "priority": "high"
    })
    return state


def log_decision_node(state: dict) -> dict:
    """Audit log — every agent run logged to PostgreSQL."""
    order = state.get("current_order")
    if not order:
        return state
    log_agent_decision.invoke({
        "order_id":      order["order_id"],
        "decision_type": state["classification"]["issue_type"],
        "reasoning":     state["classification"]["reason"],
        "action_taken":  "alert_sent" if state.get("alert_sent") else "logged_only",
        "llm_used":      state.get("llm_used", "unknown"),
        "latency_ms":    state.get("latency_ms", 0)
    })
    return state
```

---

## Sprint 9 — Supporting Services

### Story 9.1 — Database connection
**Tasks:**
1. Create `db/connection.py`:
```python
import psycopg2
from contextlib import contextmanager
import os
from dotenv import load_dotenv
load_dotenv()


@contextmanager
def get_db_connection():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    try:
        yield conn
    finally:
        conn.close()
```

### Story 9.2 — Twilio WhatsApp alert service
**Tasks:**
1. Create `services/alert_service.py`:
```python
from twilio.rest import Client
import os
from dotenv import load_dotenv
load_dotenv()


def send_whatsapp_alert(message: str) -> bool:
    """Send WhatsApp message via Twilio sandbox."""
    try:
        client = Client(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN")
        )
        client.messages.create(
            body=message,
            from_=os.getenv("TWILIO_WHATSAPP_FROM"),
            to=os.getenv("MERCHANT_WHATSAPP_TO")
        )
        return True
    except Exception as e:
        print(f"[alert_service] WhatsApp send failed: {e}")
        return False
```

---

## Sprint 10 — FastAPI Backend

### Story 10.1 — FastAPI app and all routes
**Tasks:**
1. Create `api/main.py`:
```python
from fastapi import FastAPI
from api.routes import orders, alerts, agent

app = FastAPI(title="ShipAgent API", version="1.0.0")

app.include_router(orders.router, prefix="/orders", tags=["orders"])
app.include_router(alerts.router, prefix="/alerts",  tags=["alerts"])
app.include_router(agent.router,  prefix="/agent",   tags=["agent"])


@app.get("/health")
def health():
    return {"status": "ok"}
```

2. Create `api/routes/orders.py`:
```python
from fastapi import APIRouter
from db.connection import get_db_connection

router = APIRouter()


@router.get("/")
def list_orders():
    """Return all orders from the database."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT order_id, merchant_id, status, courier, awb, attempts,
                       rto_risk_score, payment_method, delivery_city, amount,
                       updated_at, created_at
                FROM orders ORDER BY created_at DESC LIMIT 100
            """)
            rows = cur.fetchall()
            cols = ["order_id", "merchant_id", "status", "courier", "awb", "attempts",
                    "rto_risk_score", "payment_method", "delivery_city", "amount",
                    "updated_at", "created_at"]
            return [dict(zip(cols, r)) for r in rows]


@router.get("/{order_id}")
def get_order(order_id: str):
    """Return a single order by ID."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM orders WHERE order_id = %s", (order_id,))
            row = cur.fetchone()
            if not row:
                return {"error": f"Order {order_id} not found"}
            cols = [desc[0] for desc in cur.description]
            return dict(zip(cols, row))
```

3. Create `api/routes/alerts.py`:
```python
from fastapi import APIRouter
from db.connection import get_db_connection

router = APIRouter()


@router.get("/")
def list_alerts():
    """Return recent alert history."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT order_id, alert_type, channel, message, sent_at, status
                FROM alerts ORDER BY sent_at DESC LIMIT 50
            """)
            rows = cur.fetchall()
            cols = ["order_id", "alert_type", "channel", "message", "sent_at", "status"]
            return [dict(zip(cols, r)) for r in rows]
```

4. Create `api/routes/agent.py`:
```python
from fastapi import APIRouter
from agent.graph import agent_graph
from db.connection import get_db_connection

router = APIRouter()


@router.post("/run")
async def run_agent():
    """Manually trigger one agent cycle."""
    initial_state = {
        "orders_to_process": [],
        "current_order":     None,
        "classification":    None,
        "rto_assessment":    None,
        "resolution_result": None,
        "alert_sent":        False,
        "llm_used":          "",
        "latency_ms":        0,
        "decisions":         []
    }
    result = agent_graph.invoke(initial_state)
    return {
        "status":      "completed",
        "alert_sent":  result.get("alert_sent"),
        "llm_used":    result.get("llm_used"),
        "issue_type":  result.get("classification", {}).get("issue_type"),
        "reason":      result.get("classification", {}).get("reason"),
    }


@router.get("/decisions")
def get_decisions():
    """Return recent agent decisions from audit log."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT order_id, decision_type, reasoning, action_taken,
                       llm_used, latency_ms, created_at
                FROM agent_decisions ORDER BY created_at DESC LIMIT 50
            """)
            rows = cur.fetchall()
            cols = ["order_id", "decision_type", "reasoning", "action_taken",
                    "llm_used", "latency_ms", "created_at"]
            return [dict(zip(cols, r)) for r in rows]
```

5. Create `api/models.py`:
```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class OrderResponse(BaseModel):
    order_id:       str
    merchant_id:    str
    status:         str
    courier:        Optional[str]
    awb:            Optional[str]
    attempts:       int
    rto_risk_score: float
    payment_method: Optional[str]
    delivery_city:  Optional[str]
    amount:         Optional[float]
    updated_at:     Optional[datetime]
    created_at:     Optional[datetime]
```

---

## Sprint 11 — Seed Data, End-to-End Test and Final Commit

### Story 11.1 — Seed test orders
**Tasks:**
1. Create `tests/seed_orders.py`:
```python
"""Seed PostgreSQL with test orders covering all anomaly types."""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.connection import get_db_connection
from datetime import datetime, timedelta


def seed():
    TEST_ORDERS = [
        # Stuck order — not updated in 30 hours
        {
            "order_id":      "ORD-001",
            "merchant_id":   "M001",
            "status":        "in_transit",
            "courier":       "BlueDart",
            "awb":           "BD123456",
            "attempts":      0,
            "rto_risk_score": 0.1,
            "payment_method": "prepaid",
            "delivery_city": "Mumbai",
            "amount":        1500.0,
            "updated_at":    datetime.now() - timedelta(hours=30),
        },
        # High RTO risk — COD, multiple attempts, tier-3 city
        {
            "order_id":      "ORD-002",
            "merchant_id":   "M001",
            "status":        "out_for_delivery",
            "courier":       "Delhivery",
            "awb":           "DL789012",
            "attempts":      2,
            "rto_risk_score": 0.85,
            "payment_method": "cod",
            "delivery_city": "Patna",
            "amount":        2500.0,
            "updated_at":    datetime.now() - timedelta(hours=6),
        },
        # SLA breach — in transit for 10+ hours past SLA
        {
            "order_id":      "ORD-003",
            "merchant_id":   "M002",
            "status":        "in_transit",
            "courier":       "DTDC",
            "awb":           "DT345678",
            "attempts":      0,
            "rto_risk_score": 0.2,
            "payment_method": "prepaid",
            "delivery_city": "Bangalore",
            "amount":        800.0,
            "updated_at":    datetime.now() - timedelta(hours=10),
        },
        # Normal order — recent, no issues
        {
            "order_id":      "ORD-004",
            "merchant_id":   "M002",
            "status":        "packed",
            "courier":       "Ekart",
            "awb":           "EK901234",
            "attempts":      0,
            "rto_risk_score": 0.05,
            "payment_method": "prepaid",
            "delivery_city": "Delhi",
            "amount":        1200.0,
            "updated_at":    datetime.now() - timedelta(hours=2),
        },
    ]

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            for o in TEST_ORDERS:
                cur.execute("""
                    INSERT INTO orders
                        (order_id, merchant_id, status, courier, awb, attempts,
                         rto_risk_score, payment_method, delivery_city, amount, updated_at)
                    VALUES
                        (%(order_id)s, %(merchant_id)s, %(status)s, %(courier)s, %(awb)s,
                         %(attempts)s, %(rto_risk_score)s, %(payment_method)s,
                         %(delivery_city)s, %(amount)s, %(updated_at)s)
                    ON CONFLICT (order_id) DO NOTHING
                """, o)
            conn.commit()
    print(f"Seeded {len(TEST_ORDERS)} test orders.")


if __name__ == "__main__":
    seed()
```
2. Run: `python tests/seed_orders.py`

### Story 11.2 — End-to-end test
**Tasks:**
1. Confirm infrastructure is up: `docker compose up postgres redis -d`
2. Confirm knowledge base is seeded (8 chunks): 
```bash
docker compose exec postgres psql -U shipagent -d shipagent_db -c "SELECT COUNT(*) FROM knowledge_chunks;"
```
3. Confirm test orders are seeded (4 rows):
```bash
docker compose exec postgres psql -U shipagent -d shipagent_db -c "SELECT order_id, status FROM orders;"
```
4. Start API: `uvicorn api.main:app --reload`
5. Verify health: `curl http://localhost:8000/health` → `{"status":"ok"}`
6. Trigger the agent:
```bash
curl -X POST http://localhost:8000/agent/run
```
7. Expected: JSON with `alert_sent=true` and `issue_type` matching ORD-001 or ORD-002
8. Check your WhatsApp — alert should arrive for the anomalous order
9. Check decision audit log:
```bash
curl http://localhost:8000/agent/decisions
```
10. Verify: `llm_used` shows `claude-haiku-4-5-20251001` for classification and `claude-sonnet-4-6` for alerts
11. Check orders list: `curl http://localhost:8000/orders/`
12. Check alert history: `curl http://localhost:8000/alerts/`

### Story 11.3 — Final commit
**Tasks:**
1. `git add -A`
2. `git commit -m "feat: complete ShipAgent — LangGraph + RAG agentic order intelligence system"`
3. `git push`
4. Add to README a "Demo" section with:
   - Architecture diagram (ASCII is fine — see below)
   - One screenshot of the WhatsApp alert received
   - One screenshot of `/agent/decisions` API response showing audit trail
   - One screenshot of `/orders/` listing

---

## Architecture Diagram

```
Scheduled trigger (every 5 min)
        ↓
poll_orders_node (PostgreSQL query)
        ↓
classify_anomaly_node
  ├── RAG: pgvector cosine search → courier policies + historical cases
  └── Claude Haiku classification (fast + cheap, RAG context injected)
        ↓
route_anomaly_node (conditional edges, no LLM)
        ↓
┌─────────────────────────────────────────────┐
│ STUCK_ORDER     → resolve_stuck_node        │
│ HIGH_RTO_RISK   → assess_rto_node (Sonnet)  │
│ SLA_BREACH      → send_alert_node (Sonnet)  │
│ PAYMENT_ANOMALY → escalate_node             │
│ NORMAL          → log_decision_node         │
└─────────────────────────────────────────────┘
        ↓
send_alert_node (Claude Sonnet → Twilio WhatsApp)
        ↓
log_decision_node (PostgreSQL audit trail)
        ↓
END
```

---

## Definition of Done
- [ ] `docker compose up postgres redis -d` starts without error
- [ ] `docker compose exec postgres psql -U shipagent -d shipagent_db -c "\dt"` shows all 4 tables including `knowledge_chunks`
- [ ] `python scripts/seed_knowledge.py` seeds 8 chunks; `SELECT COUNT(*) FROM knowledge_chunks` returns 8
- [ ] `python tests/seed_orders.py` seeds 4 test orders
- [ ] `GET /health` returns `{"status": "ok"}`
- [ ] `POST /agent/run` returns JSON with correct `issue_type` for the seeded anomalous orders
- [ ] WhatsApp alert received on merchant number for at least one anomalous order
- [ ] `GET /agent/decisions` returns audit log showing Haiku for classification, Sonnet for alerts
- [ ] `GET /orders/` and `GET /alerts/` both return data without errors
- [ ] PostgreSQL `agent_decisions` table has rows after agent run
- [ ] `llm_router.py` has documented reasoning for each model choice
- [ ] All secrets in `.env` — nothing committed to git
- [ ] Repository pushed to GitHub with README showing architecture diagram