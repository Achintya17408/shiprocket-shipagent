from fastapi import FastAPI

from api.routes import agent, alerts, orders

app = FastAPI(title="ShipAgent API", version="1.0.0")

app.include_router(orders.router, prefix="/orders", tags=["orders"])
app.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
app.include_router(agent.router, prefix="/agent", tags=["agent"])


@app.get("/health")
def health():
    return {"status": "ok"}
