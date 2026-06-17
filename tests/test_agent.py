import json
from datetime import datetime, timedelta

from agent.graph import build_agent_graph
from agent.llm_router import classify_with_haiku, summarise_with_sonnet
from services.rto_predictor import calculate_rule_based_rto_score


def test_offline_classifier_detects_high_rto_risk(monkeypatch):
    monkeypatch.setenv("SHIPAGENT_OFFLINE_MODE", "true")
    prompt = (
        "Order data:\n"
        + json.dumps(
            {
                "order_id": "ORD-002",
                "status": "out_for_delivery",
                "payment_method": "cod",
                "delivery_city": "Patna",
                "attempts": 2,
                "amount": 2500,
                "rto_risk_score": 0.85,
            }
        )
        + "\nRelevant context retrieved from courier policies and historical case resolutions:\nDelhivery tier-3 RTO risk"
    )
    result = classify_with_haiku(prompt)
    payload = json.loads(result["result"])
    assert result["model"] == "claude-haiku-4-5-20251001"
    assert payload["issue_type"] == "HIGH_RTO_RISK"


def test_offline_sonnet_returns_rto_json(monkeypatch):
    monkeypatch.setenv("SHIPAGENT_OFFLINE_MODE", "true")
    result = summarise_with_sonnet(
        """
        Return a JSON:
        Payment method: cod
        Delivery attempts: 2
        """
    )
    payload = json.loads(result["result"])
    assert result["model"] == "claude-sonnet-4-6"
    assert payload["rto_risk_score"] >= 0.7


def test_rule_based_rto_score_flags_cod_attempts():
    assessment = calculate_rule_based_rto_score(
        {
            "payment_method": "cod",
            "delivery_city": "Patna",
            "attempts": 2,
            "amount": 2500,
            "updated_at": datetime.now() - timedelta(hours=6),
        }
    )
    assert assessment["rto_risk_score"] >= 0.7
    assert "COD" in assessment["primary_risk_factor"]


def test_graph_compiles():
    graph = build_agent_graph()
    assert graph is not None
