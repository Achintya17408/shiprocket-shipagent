"""Seed the pgvector knowledge base with courier SLA policies and historical cases."""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.rag_service import add_knowledge_chunk
from db.connection import get_db_connection

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
            "Delivered on attempt 3. Customer was unreachable - address pin needed update."
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


def seed() -> None:
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM knowledge_chunks WHERE source IN ('courier_policy', 'past_case')")
            conn.commit()

    print("Seeding courier policies into pgvector knowledge base...")
    for item in COURIER_POLICIES:
        add_knowledge_chunk(**item)
        print(f"  [OK] {item['content'][:70]}...")

    print("\nSeeding historical case resolutions...")
    for item in HISTORICAL_CASES:
        add_knowledge_chunk(**item)
        print(f"  [OK] {item['content'][:70]}...")

    print("\nKnowledge base seeded successfully. 8 chunks embedded and stored.")


if __name__ == "__main__":
    seed()
