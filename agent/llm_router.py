"""
LLM Router - decides which model to use per task type.

Decision logic:
- Haiku -> fast classification tasks (<200ms latency target, <$0.001/call)
- Sonnet -> complex reasoning, multi-step summaries, merchant-facing output
- GPT-4o-mini -> fallback when Anthropic is rate-limited, or for comparison
"""

import json
import os
import re
import time
from typing import Any

from anthropic import Anthropic
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

HAIKU = "claude-haiku-4-5-20251001"
SONNET = "claude-sonnet-4-6"
GPT_MINI = "gpt-4o-mini"


def _has_real_key(value: str | None, placeholder: str) -> bool:
    return bool(value and value.strip() and value.strip() != placeholder and "..." not in value)


def _offline_mode() -> bool:
    configured = os.getenv("SHIPAGENT_OFFLINE_MODE", "true").lower() in {"1", "true", "yes"}
    has_anthropic = _has_real_key(os.getenv("ANTHROPIC_API_KEY"), "sk-ant-...")
    has_openai = _has_real_key(os.getenv("OPENAI_API_KEY"), "sk-...")
    return configured or not (has_anthropic and has_openai)


def _extract_order(prompt: str) -> dict[str, Any]:
    match = re.search(r"Order data:\s*(\{.*?\})\s*Relevant context", prompt, re.S)
    if not match:
        return {}
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return {}


def _offline_classification(prompt: str, start: float) -> dict:
    order = _extract_order(prompt)
    status = str(order.get("status", "")).lower()
    payment_method = str(order.get("payment_method", "")).lower()
    city = str(order.get("delivery_city", "")).lower()
    attempts = int(order.get("attempts") or 0)
    risk = float(order.get("rto_risk_score") or 0)
    amount = float(order.get("amount") or 0)

    tier_3 = {"patna", "varanasi", "agra"}
    if "cod" in payment_method and (attempts > 1 or risk >= 0.7) and (amount >= 1500 or city in tier_3):
        issue = {
            "issue_type": "HIGH_RTO_RISK",
            "confidence": 0.9,
            "reason": "COD shipment with repeated attempts and courier context indicates elevated RTO risk.",
        }
    elif status in {"in_transit", "picked_up", "out_for_delivery"}:
        issue = {
            "issue_type": "STUCK_ORDER",
            "confidence": 0.82,
            "reason": "Shipment has not updated within the configured stuck-order window.",
        }
    elif "payment" in status:
        issue = {
            "issue_type": "PAYMENT_ANOMALY",
            "confidence": 0.78,
            "reason": "Payment status requires human review before fulfilment action.",
        }
    else:
        issue = {"issue_type": "NORMAL", "confidence": 0.95, "reason": "No anomaly detected."}

    return {
        "result": json.dumps(issue),
        "model": HAIKU,
        "latency_ms": int((time.time() - start) * 1000),
        "success": True,
        "offline": True,
    }


def _offline_summary(prompt: str, start: float) -> dict:
    if "Return a JSON" in prompt:
        attempts = int(re.search(r"Delivery attempts: (\d+)", prompt).group(1)) if re.search(r"Delivery attempts: (\d+)", prompt) else 0
        payment = re.search(r"Payment method: (.+)", prompt)
        payment_method = payment.group(1).strip().lower() if payment else "unknown"
        score = 0.85 if payment_method == "cod" and attempts > 1 else 0.45
        result = {
            "rto_risk_score": score,
            "primary_risk_factor": "COD with multiple delivery attempts" if score >= 0.7 else "low attempt count",
            "recommendation": "Call the customer and confirm availability before the next delivery attempt.",
        }
    else:
        issue = re.search(r"Issue: (.+)", prompt)
        order = re.search(r"Order ID: (.+)", prompt)
        issue_type = issue.group(1).strip() if issue else "Order issue"
        order_id = order.group(1).strip() if order else "unknown"
        return {
            "result": f"{issue_type}: Order {order_id} needs attention. Review the shipment and contact the customer or courier to prevent delay or RTO.",
            "model": SONNET,
            "latency_ms": int((time.time() - start) * 1000),
            "success": True,
            "offline": True,
        }

    return {
        "result": json.dumps(result),
        "model": SONNET,
        "latency_ms": int((time.time() - start) * 1000),
        "success": True,
        "offline": True,
    }


def classify_with_haiku(prompt: str) -> dict:
    """Use Haiku for anomaly classification, risk scoring, and intent detection."""
    start = time.time()
    if _offline_mode():
        return _offline_classification(prompt, start)

    try:
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        response = client.messages.create(
            model=HAIKU,
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        return {
            "result": response.content[0].text,
            "model": HAIKU,
            "latency_ms": int((time.time() - start) * 1000),
            "success": True,
        }
    except Exception as exc:
        return fallback_to_gpt(prompt, error=str(exc))


def summarise_with_sonnet(prompt: str) -> dict:
    """Use Sonnet for merchant alert summaries and multi-step reasoning."""
    start = time.time()
    if _offline_mode():
        return _offline_summary(prompt, start)

    try:
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        response = client.messages.create(
            model=SONNET,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        return {
            "result": response.content[0].text,
            "model": SONNET,
            "latency_ms": int((time.time() - start) * 1000),
            "success": True,
        }
    except Exception as exc:
        return fallback_to_gpt(prompt, error=str(exc))


def fallback_to_gpt(prompt: str, error: str = "") -> dict:
    """Fallback to GPT-4o-mini when Anthropic is unavailable."""
    start = time.time()
    if not _has_real_key(os.getenv("OPENAI_API_KEY"), "sk-..."):
        result = _offline_summary(prompt, start) if "Issue:" in prompt or "Return a JSON" in prompt else _offline_classification(prompt, start)
        result["model"] = GPT_MINI
        result["fallback_reason"] = error or "missing OpenAI API key"
        return result

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model=GPT_MINI,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
    )
    return {
        "result": response.choices[0].message.content,
        "model": GPT_MINI,
        "latency_ms": int((time.time() - start) * 1000),
        "success": True,
        "fallback_reason": error,
    }
