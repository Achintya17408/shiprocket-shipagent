from fastapi import APIRouter

from agent.graph import agent_graph
from db.connection import get_db_connection

router = APIRouter()


def _initial_state() -> dict:
    return {
        "orders_to_process": [],
        "current_order": None,
        "classification": None,
        "rto_assessment": None,
        "resolution_result": None,
        "alert_sent": False,
        "llm_used": "",
        "latency_ms": 0,
        "decisions": [],
    }


@router.post("/run")
async def run_agent():
    """Manually trigger one agent cycle."""
    result = agent_graph.invoke(_initial_state())
    classification = result.get("classification") or {}
    return {
        "status": "completed",
        "processed_order": (result.get("current_order") or {}).get("order_id"),
        "alert_sent": result.get("alert_sent"),
        "llm_used": result.get("llm_used"),
        "issue_type": classification.get("issue_type"),
        "reason": classification.get("reason"),
    }


@router.get("/decisions")
def get_decisions():
    """Return recent agent decisions from audit log."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT order_id, decision_type, reasoning, action_taken,
                       llm_used, latency_ms, created_at
                FROM agent_decisions ORDER BY created_at DESC LIMIT 50
                """
            )
            rows = cur.fetchall()
            cols = ["order_id", "decision_type", "reasoning", "action_taken", "llm_used", "latency_ms", "created_at"]
            return [dict(zip(cols, row)) for row in rows]
