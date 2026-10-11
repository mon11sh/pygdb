"""
Notification Service - Async Notification Handling

Handles sending and storing notifications asynchronously.

Author: GDB Architecture Team
"""

from app.models.notification import NotificationRequest
from app.services.notification_storage_service import storage
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NotificationService")


class NotificationService:
    """
    Async notification service.
    Handles sending and storing in-app notifications.
    """
    
    async def send_notification(self, request: NotificationRequest) -> bool:
        """
        Send an in-app notification and store it asynchronously.
        
        Args:
            request: NotificationRequest with recipient, message, type, and mode
            
        Returns:
            True if notification was sent successfully
        """
        logger.info(f"[NOTIFICATION] To: {request.recipient} | Type: {request.type} | Msg: {request.message}")
        
        # Store for Frontend (async)
        await storage.add_notification(
            recipient=request.recipient, 
            message=request.message, 
            type=request.type.value,
            mode=request.mode
        )
        return True


notify_service = NotificationService()
