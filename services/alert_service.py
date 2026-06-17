import os

from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()


def _has_twilio_config() -> bool:
    required = [
        os.getenv("TWILIO_ACCOUNT_SID"),
        os.getenv("TWILIO_AUTH_TOKEN"),
        os.getenv("TWILIO_WHATSAPP_FROM"),
        os.getenv("MERCHANT_WHATSAPP_TO"),
    ]
    return all(value and "..." not in value and "xxxx" not in value.lower() for value in required)


def send_whatsapp_alert(message: str) -> bool:
    """Send WhatsApp message via Twilio sandbox."""
    if os.getenv("SHIPAGENT_OFFLINE_MODE", "true").lower() in {"1", "true", "yes"} or not _has_twilio_config():
        print(f"[alert_service] Offline WhatsApp alert: {message}")
        return True

    try:
        client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
        client.messages.create(
            body=message,
            from_=os.getenv("TWILIO_WHATSAPP_FROM"),
            to=os.getenv("MERCHANT_WHATSAPP_TO"),
        )
        return True
    except Exception as exc:
        print(f"[alert_service] WhatsApp send failed: {exc}")
        return False
