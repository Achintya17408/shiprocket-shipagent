from fastapi import APIRouter, HTTPException

from db.connection import get_db_connection

router = APIRouter()


@router.get("/")
def list_orders():
    """Return all orders from the database."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT order_id, merchant_id, status, courier, awb, attempts,
                       rto_risk_score, payment_method, delivery_city, amount,
                       updated_at, created_at
                FROM orders ORDER BY created_at DESC LIMIT 100
                """
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
            return [dict(zip(cols, row)) for row in rows]


@router.get("/{order_id}")
def get_order(order_id: str):
    """Return a single order by ID."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM orders WHERE order_id = %s", (order_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
            cols = [desc[0] for desc in cur.description]
            return dict(zip(cols, row))
