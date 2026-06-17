from fastapi import APIRouter

from db.connection import get_db_connection

router = APIRouter()


@router.get("/")
def list_alerts():
    """Return recent alert history."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT order_id, alert_type, channel, recipient, message, sent_at, status
                FROM alerts ORDER BY sent_at DESC LIMIT 50
                """
            )
            rows = cur.fetchall()
            cols = ["order_id", "alert_type", "channel", "recipient", "message", "sent_at", "status"]
            return [dict(zip(cols, row)) for row in rows]
