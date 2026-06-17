"""Seed PostgreSQL with test orders covering all anomaly types."""

import os
import sys
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.connection import get_db_connection


TEST_ORDERS = [
    {
        "order_id": "ORD-001",
        "merchant_id": "M001",
        "status": "in_transit",
        "courier": "BlueDart",
        "awb": "BD123456",
        "attempts": 0,
        "rto_risk_score": 0.1,
        "payment_method": "prepaid",
        "delivery_city": "Mumbai",
        "amount": 1500.0,
        "updated_at": datetime.now() - timedelta(hours=30),
    },
    {
        "order_id": "ORD-002",
        "merchant_id": "M001",
        "status": "out_for_delivery",
        "courier": "Delhivery",
        "awb": "DL789012",
        "attempts": 2,
        "rto_risk_score": 0.85,
        "payment_method": "cod",
        "delivery_city": "Patna",
        "amount": 2500.0,
        "updated_at": datetime.now() - timedelta(hours=6),
    },
    {
        "order_id": "ORD-003",
        "merchant_id": "M002",
        "status": "in_transit",
        "courier": "DTDC",
        "awb": "DT345678",
        "attempts": 0,
        "rto_risk_score": 0.2,
        "payment_method": "prepaid",
        "delivery_city": "Bangalore",
        "amount": 800.0,
        "updated_at": datetime.now() - timedelta(hours=10),
    },
    {
        "order_id": "ORD-004",
        "merchant_id": "M002",
        "status": "packed",
        "courier": "Ekart",
        "awb": "EK901234",
        "attempts": 0,
        "rto_risk_score": 0.05,
        "payment_method": "prepaid",
        "delivery_city": "Delhi",
        "amount": 1200.0,
        "updated_at": datetime.now() - timedelta(hours=2),
    },
]


def seed() -> None:
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            for order in TEST_ORDERS:
                cur.execute(
                    """
                    INSERT INTO orders
                        (order_id, merchant_id, status, courier, awb, attempts,
                         rto_risk_score, payment_method, delivery_city, amount, updated_at)
                    VALUES
                        (%(order_id)s, %(merchant_id)s, %(status)s, %(courier)s, %(awb)s,
                         %(attempts)s, %(rto_risk_score)s, %(payment_method)s,
                         %(delivery_city)s, %(amount)s, %(updated_at)s)
                    ON CONFLICT (order_id) DO UPDATE SET
                        status = EXCLUDED.status,
                        courier = EXCLUDED.courier,
                        awb = EXCLUDED.awb,
                        attempts = EXCLUDED.attempts,
                        rto_risk_score = EXCLUDED.rto_risk_score,
                        payment_method = EXCLUDED.payment_method,
                        delivery_city = EXCLUDED.delivery_city,
                        amount = EXCLUDED.amount,
                        updated_at = EXCLUDED.updated_at
                    """,
                    order,
                )
            conn.commit()
    print(f"Seeded {len(TEST_ORDERS)} test orders.")


if __name__ == "__main__":
    seed()
