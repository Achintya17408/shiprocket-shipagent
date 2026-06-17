import os
import time

import redis
from dotenv import load_dotenv

from agent.graph import agent_graph

load_dotenv()


def run_once() -> dict:
    initial_state = {
        "orders_to_process": [],
        "current_order": None,
        "classification": None,
        "rto_assessment": None,
        "resolution_result": None,
        "alert_sent": False,
        "llm_used": "",
        "latency_ms": 0,
        "classification_llm_used": "",
        "classification_latency_ms": 0,
        "assessment_llm_used": "",
        "assessment_latency_ms": 0,
        "alert_llm_used": "",
        "alert_latency_ms": 0,
        "decisions": [],
    }
    return agent_graph.invoke(initial_state)


def run_forever() -> None:
    interval = int(os.getenv("POLL_INTERVAL_SECONDS", 300))
    client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    while True:
        client.set("shipagent:last_poll_started", int(time.time()))
        run_once()
        client.set("shipagent:last_poll_finished", int(time.time()))
        time.sleep(interval)


if __name__ == "__main__":
    run_forever()
