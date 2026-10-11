"""
Notification API Routes - Async Endpoints

FastAPI routes for notification operations.
All endpoints are async for non-blocking I/O.

Author: GDB Architecture Team
"""

from fastapi import APIRouter, HTTPException, Depends
from app.models.notification import NotificationRequest
from app.services.notification_service import NotificationService
from app.services.notification_storage_service import storage
from app.dependencies.providers import get_notification_service

router = APIRouter()


@router.post("/send")
async def send_notification(
    request: NotificationRequest,
    service: NotificationService = Depends(get_notification_service)
):
    """Send a notification asynchronously."""
    try:
        await service.send_notification(request)
        return {"status": "sent", "type": request.type}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{identifier}")
async def get_notifications(identifier: str):
    """Get notifications for a specific user asynchronously."""
    return await storage.get_notifications(identifier)


@router.post("/read/{identifier}")
async def mark_as_read(identifier: str):
    """Mark all notifications as read asynchronously."""
    await storage.mark_all_as_read(identifier)
    return {"status": "success", "message": f"Notifications for {identifier} marked as read"}


@router.delete("/{identifier}")
async def clear_notifications(identifier: str):
    """Clear all notifications asynchronously."""
    await storage.clear_notifications(identifier)
    return {"status": "success", "message": f"Notifications for {identifier} cleared"}
