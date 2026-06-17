"""
RAG Service - retrieves relevant context before LLM classification.

Uses pgvector on PostgreSQL. In local offline mode, embeddings are deterministic
1536-dim vectors so the full flow can be tested before API keys are configured.
"""

import hashlib
import json
import os
from math import sqrt

from dotenv import load_dotenv
from openai import OpenAI

from db.connection import get_db_connection

load_dotenv()

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
RAG_TOP_K = int(os.getenv("RAG_TOP_K", 3))


def _has_real_key(value: str | None) -> bool:
    return bool(value and value.strip() and "..." not in value)


def _offline_mode() -> bool:
    return os.getenv("SHIPAGENT_OFFLINE_MODE", "true").lower() in {"1", "true", "yes"} or not _has_real_key(os.getenv("OPENAI_API_KEY"))


def _deterministic_embedding(text: str) -> list[float]:
    values: list[float] = []
    counter = 0
    while len(values) < 1536:
        digest = hashlib.sha256(f"{counter}:{text}".encode("utf-8")).digest()
        values.extend((byte / 127.5) - 1.0 for byte in digest)
        counter += 1
    vector = values[:1536]
    norm = sqrt(sum(v * v for v in vector)) or 1.0
    return [v / norm for v in vector]


def get_embedding(text: str) -> list[float]:
    """Convert text to a 1536-dim vector using OpenAI or local deterministic mode."""
    if _offline_mode():
        return _deterministic_embedding(text)

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=text)
    return response.data[0].embedding


def retrieve_relevant_context(query: str, top_k: int = RAG_TOP_K) -> str:
    """Retrieve top-k semantically similar chunks from knowledge_chunks."""
    embedding = get_embedding(query)
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT content, source,
                       1 - (embedding <=> %s::vector) AS similarity
                FROM knowledge_chunks
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (embedding, embedding, top_k),
            )
            rows = cur.fetchall()

    if not rows:
        return "No relevant context found in knowledge base."
    return "\n\n".join(f"[{r[1]}] (similarity: {float(r[2]):.2f}): {r[0]}" for r in rows)


def add_knowledge_chunk(source: str, content: str, metadata: dict | None = None) -> None:
    """Embed and store a knowledge chunk into the pgvector knowledge base."""
    embedding = get_embedding(content)
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO knowledge_chunks (source, content, embedding, metadata)
                VALUES (%s, %s, %s::vector, %s::jsonb)
                """,
                (source, content, embedding, json.dumps(metadata or {})),
            )
            conn.commit()
