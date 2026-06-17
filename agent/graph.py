"""
LangGraph state machine for ShipAgent.

Flow:
poll_orders -> classify_anomaly -> route_anomaly -> handler -> send_alert/log -> END
"""

from typing import List, Optional, TypedDict

from langgraph.graph import END, StateGraph

from agent.nodes import (
    assess_rto_risk_node,
    classify_anomaly_node,
    escalate_node,
    log_decision_node,
    poll_orders_node,
    resolve_stuck_order_node,
    route_anomaly_node,
    send_alert_node,
)


class AgentState(TypedDict):
    orders_to_process: List[dict]
    current_order: Optional[dict]
    classification: Optional[dict]
    rto_assessment: Optional[dict]
    resolution_result: Optional[str]
    alert_sent: bool
    llm_used: str
    latency_ms: int
    decisions: List[dict]


def _route_issue(state: AgentState) -> str:
    classification = state.get("classification") or {"issue_type": "NORMAL"}
    return classification.get("issue_type", "NORMAL")


def build_agent_graph():
    graph = StateGraph(AgentState)

    graph.add_node("poll_orders", poll_orders_node)
    graph.add_node("classify_anomaly", classify_anomaly_node)
    graph.add_node("route_anomaly", route_anomaly_node)
    graph.add_node("resolve_stuck", resolve_stuck_order_node)
    graph.add_node("assess_rto", assess_rto_risk_node)
    graph.add_node("send_alert", send_alert_node)
    graph.add_node("escalate", escalate_node)
    graph.add_node("log_decision", log_decision_node)

    graph.set_entry_point("poll_orders")
    graph.add_edge("poll_orders", "classify_anomaly")
    graph.add_edge("classify_anomaly", "route_anomaly")
    graph.add_conditional_edges(
        "route_anomaly",
        _route_issue,
        {
            "STUCK_ORDER": "resolve_stuck",
            "HIGH_RTO_RISK": "assess_rto",
            "SLA_BREACH": "send_alert",
            "PAYMENT_ANOMALY": "escalate",
            "NORMAL": "log_decision",
        },
    )
    graph.add_edge("resolve_stuck", "send_alert")
    graph.add_edge("assess_rto", "send_alert")
    graph.add_edge("send_alert", "log_decision")
    graph.add_edge("escalate", "log_decision")
    graph.add_edge("log_decision", END)

    return graph.compile()


agent_graph = build_agent_graph()
