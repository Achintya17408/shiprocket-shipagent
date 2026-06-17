import json
from datetime import datetime, timedelta

from agent.graph import build_agent_graph
import agent.llm_router as llm_router
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


class _FakeAnthropicContent:
    text = '{"issue_type":"NORMAL","confidence":0.99,"reason":"mocked real-mode Claude call"}'


class _FakeAnthropicResponse:
    content = [_FakeAnthropicContent()]


class _FakeMessages:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return _FakeAnthropicResponse()


class _FakeAnthropic:
    last_instance = None

    def __init__(self, api_key):
        self.api_key = api_key
        self.messages = _FakeMessages()
        _FakeAnthropic.last_instance = self


class _FakeEmbeddingDatum:
    embedding = [0.0] * 1536


class _FakeEmbeddingResponse:
    data = [_FakeEmbeddingDatum()]


class _FakeEmbeddings:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return _FakeEmbeddingResponse()


class _FakeOpenAI:
    last_instance = None

    def __init__(self, api_key):
        self.api_key = api_key
        self.embeddings = _FakeEmbeddings()
        _FakeOpenAI.last_instance = self


def test_real_mode_claude_path_is_mocked_without_spending(monkeypatch):
    monkeypatch.setenv("SHIPAGENT_OFFLINE_MODE", "false")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(llm_router, "Anthropic", _FakeAnthropic)

    result = classify_with_haiku("Order data:\n{}\nRelevant context retrieved from courier policies and historical case resolutions:\nmock")

    assert result["model"] == "claude-haiku-4-5-20251001"
    assert _FakeAnthropic.last_instance.api_key == "sk-ant-test"
    assert _FakeAnthropic.last_instance.messages.calls[0]["model"] == "claude-haiku-4-5-20251001"


def test_real_mode_openai_embedding_path_is_mocked_without_spending(monkeypatch):
    import services.rag_service as rag_service

    monkeypatch.setenv("SHIPAGENT_OFFLINE_MODE", "false")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(rag_service, "OpenAI", _FakeOpenAI)

    embedding = rag_service.get_embedding("mock courier policy")

    assert len(embedding) == 1536
    assert _FakeOpenAI.last_instance.api_key == "sk-test"
    assert _FakeOpenAI.last_instance.embeddings.calls[0]["model"] == "text-embedding-3-small"
