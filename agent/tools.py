import json
import os

from langchain.tools import tool

from db.connection import get_db_connection
from services.alert_service import send_whatsapp_alert


@tool
def get_order_status(order_id: str) -> str:
    """
    Fetch the current status of an order from the database.
    Use this when the agent needs to verify order state before taking action.
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT order_id, status, courier, awb, attempts,
                       rto_risk_score, updated_at
                FROM orders WHERE order_id = %s
                """,
                (order_id,),
            )
            row = cur.fetchone()
            if not row:
                return f"Order {order_id} not found"
            cols = ["order_id", "status", "courier", "awb", "attempts", "rto_risk_score", "updated_at"]
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
                """
                UPDATE orders SET rto_risk_score = %s, status = 'rto_risk_flagged'
                WHERE order_id = %s
                """,
                (risk_score, order_id),
            )
            conn.commit()
    return f"Order {order_id} flagged as RTO risk (score: {risk_score}). Reason: {reason}"


@tool
def send_merchant_alert(order_id: str, alert_type: str, message: str) -> str:
    """
    Send a WhatsApp alert to the merchant about a critical order issue.
    Use for stuck orders, RTO risk, and SLA breach predictions.
    """
    result = send_whatsapp_alert(message)
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO alerts (order_id, alert_type, channel, recipient, message, status)
                VALUES (%s, %s, 'whatsapp', %s, %s, %s)
                """,
                (
                    order_id,
                    alert_type,
                    os.getenv("MERCHANT_WHATSAPP_TO"),
                    message,
                    "sent" if result else "failed",
                ),
            )
            conn.commit()
    return f"Alert sent for order {order_id}: {alert_type}"


@tool
def escalate_to_human(order_id: str, reason: str, priority: str) -> str:
    """
    Log an escalation for human review when the agent cannot resolve autonomously.
    Priority must be one of: low, medium, high, critical.
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO agent_decisions
                    (order_id, decision_type, reasoning, action_taken, llm_used)
                VALUES (%s, 'escalation', %s, %s, 'system')
                """,
                (order_id, reason, f"Escalated to human - priority: {priority}"),
            )
            conn.commit()
    return f"Order {order_id} escalated. Priority: {priority}. Reason: {reason}"


@tool
def log_agent_decision(order_id: str, decision_type: str, reasoning: str, action_taken: str, llm_used: str, latency_ms: int) -> str:
    """
    Log every agent decision to the audit trail in PostgreSQL.
    Must be called after every decision.
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO agent_decisions
                    (order_id, decision_type, reasoning, action_taken, llm_used, latency_ms)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (order_id, decision_type, reasoning, action_taken, llm_used, latency_ms),
            )
            conn.commit()
    return "Decision logged"


TOOLS = [get_order_status, flag_rto_risk, send_merchant_alert, escalate_to_human, log_agent_decision]
