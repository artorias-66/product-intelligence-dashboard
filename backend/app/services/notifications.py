"""Notifications service — handles sending alerts to external platforms like Telegram."""

import requests
import logging
from app.config import settings

logger = logging.getLogger(__name__)

def send_telegram_notification(message: str):
    """Sends a markdown-formatted message to the configured Telegram chat."""
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        logger.debug("Telegram notification skipped: Bot token or Chat ID not configured.")
        return

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": settings.TELEGRAM_CHAT_ID,
        "text": message
    }
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
        logger.info("Telegram notification sent successfully.")
    except Exception as e:
        logger.error(f"Failed to send Telegram notification: {e}")
