from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class OrderResponse(BaseModel):
    order_id: str
    merchant_id: str
    status: str
    courier: Optional[str]
    awb: Optional[str]
    attempts: int
    rto_risk_score: float
    payment_method: Optional[str]
    delivery_city: Optional[str]
    amount: Optional[float]
    updated_at: Optional[datetime]
    created_at: Optional[datetime]
