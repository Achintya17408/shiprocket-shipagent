ANOMALY_CLASSIFICATION_PROMPT = """
You are an order anomaly classifier for an e-commerce logistics platform.
Analyse this order and classify the issue type.

Order data:
{order_data}

Relevant context retrieved from courier policies and historical case resolutions:
{retrieved_context}

Use the retrieved context to inform your classification. For example, if the
courier has a known high RTO rate in this city, weight that appropriately.

Classify as exactly one of:
- STUCK_ORDER: order not updated for > 24 hours
- HIGH_RTO_RISK: delivery likely to fail and return (COD + remote pin code + previous attempts > 1)
- SLA_BREACH: expected delivery date passed, order not delivered
- PAYMENT_ANOMALY: COD amount mismatch or suspicious pattern
- NORMAL: no issue detected

Respond in JSON only:
{{"issue_type": "...", "confidence": 0.0-1.0, "reason": "one sentence referencing courier context if relevant"}}
"""

MERCHANT_ALERT_PROMPT = """
You are writing a WhatsApp alert for an SMB merchant using Shiprocket.
The merchant is non-technical. Be direct, helpful, and specific.
Keep it under 150 words.

Issue: {issue_type}
Order ID: {order_id}
Details: {details}

Write the alert message. Start with the issue, then what is happening,
then what the merchant should do (if anything).
"""

RTO_RISK_ASSESSMENT_PROMPT = """
Assess the RTO (Return to Origin) risk for this shipment.

Order details:
- Payment method: {payment_method}
- Delivery city: {delivery_city}
- Delivery attempts: {attempts}
- Order amount: {amount}
- Days since last update: {days_stale}

RTO risk factors:
- COD orders have 3x higher RTO rate than prepaid
- Delivery attempts > 1 strongly predicts RTO
- Remote/tier-3 cities have higher RTO rates
- High-value COD orders (> Rs.2000) have elevated risk

Return a JSON:
{{"rto_risk_score": 0.0-1.0, "primary_risk_factor": "...", "recommendation": "..."}}
"""
