CREATE EXTENSION IF NOT EXISTS vector;

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

CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id          SERIAL PRIMARY KEY,
    source      VARCHAR(100),
    content     TEXT,
    embedding   vector(1536),
    metadata    JSONB,
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_merchant ON orders(merchant_id);
CREATE INDEX IF NOT EXISTS idx_decisions_order ON agent_decisions(order_id);
CREATE INDEX IF NOT EXISTS idx_alerts_order ON alerts(order_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_embedding ON knowledge_chunks
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
