"""HTTP client for the outbound Notification Service.

Provides a thin async wrapper used by the transaction flows to push user-facing
notifications (deposit/withdrawal/transfer outcomes). Failures are swallowed and
logged so notification problems never abort a completed money movement.
"""

import httpx
import logging
from typing import Optional
from app.config.settings import settings
from app.correlation import current_correlation_id

logger = logging.getLogger(__name__)

class NotificationClient:
    """Async client that posts notification messages to the Notification Service."""

    @property
    def BASE_URL(self):
        """Base URL of the Notification Service notify API, from settings."""
        return f"{settings.NOTIFICATION_SERVICE_URL}/api/v1/notify"

    async def send_notification(self, recipient: str, message: str, type: str = "INFO", mode: Optional[str] = None):
        """Send a notification to the Notification Service (best-effort).

        Posts to the notify `/send` endpoint with the internal API key and the
        current correlation id. Any transport or server error is caught and
        logged as a warning rather than raised, so callers are never blocked.

        Args:
            recipient: Recipient identifier (typically the account number).
            message: Human-readable notification body.
            type: Notification severity/category (default "INFO").
            mode: Optional delivery/transfer mode tag.
        """
        try:
            payload = {
                "recipient": recipient,
                "message": message,
                "type": type,
                "mode": mode
            }
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self.BASE_URL}/send",
                    json=payload,
                    headers={"X-Internal-API-Key": settings.INTERNAL_API_KEY, "X-Correlation-ID": current_correlation_id()},
                    timeout=2.0,
                )
        except Exception as e:
            logger.warning(f"Failed to send notification: {str(e)}")

notification_client = NotificationClient()
