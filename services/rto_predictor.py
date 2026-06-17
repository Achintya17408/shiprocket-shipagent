import os

RTO_THRESHOLD = float(os.getenv("RTO_RISK_THRESHOLD", 0.7))
TIER_3_CITIES = {"patna", "varanasi", "agra"}
TIER_2_CITIES = {"pune", "jaipur", "lucknow", "indore"}


def calculate_rule_based_rto_score(order: dict) -> dict:
    """Small deterministic scorer used before or alongside LLM assessment."""
    score = 0.05
    reasons: list[str] = []

    if str(order.get("payment_method", "")).lower() == "cod":
        score += 0.35
        reasons.append("COD payment")

    attempts = int(order.get("attempts") or 0)
    if attempts > 1:
        score += 0.25
        reasons.append("multiple delivery attempts")
    elif attempts == 1:
        score += 0.12
        reasons.append("one failed delivery attempt")

    city = str(order.get("delivery_city", "")).lower()
    if city in TIER_3_CITIES:
        score += 0.2
        reasons.append("tier-3 delivery city")
    elif city in TIER_2_CITIES:
        score += 0.1
        reasons.append("tier-2 delivery city")

    amount = float(order.get("amount") or 0)
    if amount >= 2000 and str(order.get("payment_method", "")).lower() == "cod":
        score += 0.15
        reasons.append("high-value COD")

    final_score = min(score, 0.99)
    return {
        "rto_risk_score": final_score,
        "primary_risk_factor": ", ".join(reasons) or "no major risk factors",
        "recommendation": "Contact the customer before the next attempt." if final_score >= RTO_THRESHOLD else "Continue normal monitoring.",
    }
