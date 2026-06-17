import json
import os
import re
from datetime import datetime, timedelta
from decimal import Decimal

from agent.llm_router import classify_with_haiku, summarise_with_sonnet
from agent.prompts import ANOMALY_CLASSIFICATION_PROMPT, MERCHANT_ALERT_PROMPT, RTO_RISK_ASSESSMENT_PROMPT
from agent.tools import escalate_to_human, flag_rto_risk, log_agent_decision, send_merchant_alert
from db.connection import get_db_connection
from services.rag_service import retrieve_relevant_context
from services.rto_predictor import calculate_rule_based_rto_score

STUCK_HOURS = int(os.getenv("STUCK_ORDER_HOURS", 24))
RTO_THRESHOLD = float(os.getenv("RTO_RISK_THRESHOLD", 0.7))
VALID_ISSUES = {"STUCK_ORDER", "HIGH_RTO_RISK", "SLA_BREACH", "PAYMENT_ANOMALY", "NORMAL"}


def _json_default(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _parse_json_object(text: str, fallback: dict) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.S)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    return fallback


def poll_orders_node(state: dict) -> dict:
    """Fetch orders that need attention from PostgreSQL."""
    stuck_cutoff = datetime.now() - timedelta(hours=STUCK_HOURS)
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT order_id, merchant_id, status, courier, awb, attempts,
                       rto_risk_score, payment_method, delivery_city, amount,
                       updated_at, created_at
                FROM orders
                WHERE (updated_at < %s AND status NOT IN ('delivered','cancelled','rto_complete'))
                   OR (rto_risk_score > %s AND status != 'rto_risk_flagged')
                ORDER BY
                    CASE WHEN rto_risk_score > %s THEN 0 ELSE 1 END,
                    updated_at ASC
                LIMIT 50
                """,
                (stuck_cutoff, RTO_THRESHOLD, RTO_THRESHOLD),
            )
            rows = cur.fetchall()
            cols = [
                "order_id",
                "merchant_id",
                "status",
                "courier",
                "awb",
                "attempts",
                "rto_risk_score",
                "payment_method",
                "delivery_city",
                "amount",
                "updated_at",
                "created_at",
            ]
            orders = [dict(zip(cols, row)) for row in rows]

    state["orders_to_process"] = orders
    state["current_order"] = orders[0] if orders else None
    return state


def classify_anomaly_node(state: dict) -> dict:
    """Classify anomaly with RAG context and Claude Haiku."""
    order = state.get("current_order")
    if not order:
        state["classification"] = {"issue_type": "NORMAL", "confidence": 1.0, "reason": "No orders need attention."}
        return state

    rag_query = (
        f"{order.get('courier', '')} {order.get('delivery_city', '')} "
        f"{order.get('payment_method', '')} attempts:{order.get('attempts', 0)} amount:{order.get('amount', 0)}"
    )
    retrieved_context = retrieve_relevant_context(rag_query)
    prompt = ANOMALY_CLASSIFICATION_PROMPT.format(
        order_data=json.dumps(order, default=_json_default),
        retrieved_context=retrieved_context,
    )
    result = classify_with_haiku(prompt)
    fallback = {"issue_type": "NORMAL", "confidence": 0.5, "reason": "LLM response could not be parsed."}
    classification = _parse_json_object(result["result"], fallback)

    if classification.get("issue_type") not in VALID_ISSUES:
        classification = fallback

    state["classification"] = classification
    state["llm_used"] = result["model"]
    state["latency_ms"] = result["latency_ms"]
    return state


def route_anomaly_node(state: dict) -> dict:
    """Routing node. Conditional edges inspect the classification."""
    return state


def resolve_stuck_order_node(state: dict) -> dict:
    """Handle stuck orders by preparing a resolution summary."""
    order = state["current_order"]
    state["resolution_result"] = (
        f"Stuck order detected: {order['order_id']} last updated {order['updated_at']}. "
        "Escalate courier retry or request a hub scan update."
    )
    return state


def assess_rto_risk_node(state: dict) -> dict:
    """Use Sonnet for detailed RTO risk assessment, with deterministic scorer fallback."""
    order = state["current_order"]
    updated_at = order.get("updated_at")
    days_stale = (datetime.now() - updated_at).days if updated_at else 0

    prompt = RTO_RISK_ASSESSMENT_PROMPT.format(
        payment_method=order.get("payment_method", "unknown"),
        delivery_city=order.get("delivery_city", "unknown"),
        attempts=order.get("attempts", 0),
        amount=float(order.get("amount") or 0),
        days_stale=days_stale,
    )
    result = summarise_with_sonnet(prompt)
    assessment = _parse_json_object(result["result"], calculate_rule_based_rto_score(order))

    state["rto_assessment"] = assessment
    state["llm_used"] = result["model"]

    if float(assessment.get("rto_risk_score", 0)) >= RTO_THRESHOLD:
        flag_rto_risk.invoke(
            {
                "order_id": order["order_id"],
                "risk_score": float(assessment["rto_risk_score"]),
                "reason": assessment.get("primary_risk_factor", "risk threshold crossed"),
            }
        )
    return state


def send_alert_node(state: dict) -> dict:
    """Use Sonnet to draft a merchant-friendly WhatsApp alert."""
    order = state["current_order"]
    issue_type = state["classification"]["issue_type"]
    details = state.get("rto_assessment") or state.get("resolution_result") or state["classification"]

    prompt = MERCHANT_ALERT_PROMPT.format(
        issue_type=issue_type,
        order_id=order["order_id"],
        details=json.dumps(details, default=_json_default),
    )
    result = summarise_with_sonnet(prompt)
    send_merchant_alert.invoke(
        {
            "order_id": order["order_id"],
            "alert_type": issue_type,
            "message": result["result"],
        }
    )
    state["alert_sent"] = True
    state["llm_used"] = result["model"]
    state["latency_ms"] = result["latency_ms"]
    return state


def escalate_node(state: dict) -> dict:
    """Escalate unresolvable issues to human review."""
    order = state["current_order"]
    escalate_to_human.invoke(
        {
            "order_id": order["order_id"],
            "reason": state["classification"].get("reason", "Manual review required."),
            "priority": "high",
        }
    )
    state["resolution_result"] = "Escalated to human operations queue."
    return state


def log_decision_node(state: dict) -> dict:
    """Audit log every agent run."""
    order = state.get("current_order")
    if not order:
        return state

    log_agent_decision.invoke(
        {
            "order_id": order["order_id"],
            "decision_type": state["classification"]["issue_type"],
            "reasoning": state["classification"].get("reason", ""),
            "action_taken": "alert_sent" if state.get("alert_sent") else "logged_only",
            "llm_used": state.get("llm_used", "unknown"),
            "latency_ms": int(state.get("latency_ms") or 0),
        }
    )
    return state
