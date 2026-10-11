"""
Dependency Provider Module.

Supplies FastAPI dependency-injection factories for the notification service.
These providers are wired into route handlers via ``Depends`` so that service
instances can be constructed and, if needed, substituted during testing.

Author: GDB Architecture Team
"""

from fastapi import Depends
from app.services.notification_service import NotificationService

def get_notification_service() -> NotificationService:
    """Provide a NotificationService instance for dependency injection.

    Returns:
        NotificationService: A freshly constructed notification service used by
        route handlers to send and store notifications.
    """
    return NotificationService()
