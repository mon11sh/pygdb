"""
Notification Service Client

Handles sending notifications to the central Notification Service.
"""

import httpx
import logging
from app.config.settings import settings

logger = logging.getLogger(__name__)

class NotificationClient:
    """Client for Notification Service."""
    
    BASE_URL = f"{settings.NOTIFICATION_SERVICE_URL}/api/v1/notify"
    
    @staticmethod
    async def send_notification(user_id: str, message: str, notification_type: str = "INFO", mode: str = None):
        """
        Send a notification via Notification Service.
        """
        try:
            async with httpx.AsyncClient() as client:
                # Map to generic notifications
                response = await client.post(
                    f"{NotificationClient.BASE_URL}/send",
                    json={
                        "recipient": user_id,
                        "message": message,
                        "type": notification_type,
                        "mode": mode
                    },
                    headers={"X-Internal-API-Key": settings.INTERNAL_API_KEY},
                    timeout=5.0
                )
                if response.status_code == 200:
                    logger.info(f"✅ Notification sent to {user_id}")
                else:
                    logger.warning(f"⚠️ Failed to send notification: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Notification service error: {e}")
            # Don't fail the main process if notification fails
