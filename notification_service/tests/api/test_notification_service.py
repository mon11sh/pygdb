import pytest
from app.main import app
from httpx import ASGITransport, AsyncClient
from unittest.mock import patch, MagicMock
from app.models.notification import NotificationType

@pytest.mark.asyncio
class TestNotificationService:
    """Test suite for Notification Service"""

    BASE_URL = "/api/v1/notify"

    async def test_send_notification_success(self):
        """POSITIVE: Send notification successfully"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            with patch("app.services.notification_storage_service.storage.add_notification") as mock_add:
                response = await client.post(
                    f"{self.BASE_URL}/send",
                    json={
                        "recipient": "1234567890",
                        "message": "Test Message",
                        "type": "SUCCESS"
                    }
                )
                assert response.status_code == 200
                assert response.json()["status"] == "sent"
                assert response.json()["type"] == "SUCCESS"
                mock_add.assert_called_once()

    async def test_send_notification_with_mode(self):
        """POSITIVE: Send notification with transfer mode"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            with patch("app.services.notification_storage_service.storage.add_notification") as mock_add:
                response = await client.post(
                    f"{self.BASE_URL}/send",
                    json={
                        "recipient": "1234567890",
                        "message": "Received ₹500.0 via UPI",
                        "type": "SUCCESS",
                        "mode": "UPI"
                    }
                )
                assert response.status_code == 200
                assert response.json()["status"] == "sent"
                # Verify that mode was passed to the storage service
                mock_add.assert_called_once_with(
                    recipient="1234567890",
                    message="Received ₹500.0 via UPI",
                    type="SUCCESS",
                    mode="UPI"
                )

    async def test_get_notifications(self):
        """POSITIVE: Get notifications for a user"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            mock_data = [
                {"id": 1, "recipient": "1234567890", "message": "Test 1", "type": "INFO", "read": False}
            ]
            with patch("app.services.notification_storage_service.storage.get_notifications", return_value=mock_data):
                response = await client.get(f"{self.BASE_URL}/1234567890")
                assert response.status_code == 200
                assert len(response.json()) == 1
                assert response.json()[0]["message"] == "Test 1"

    async def test_mark_as_read(self):
        """POSITIVE: Mark notifications as read"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            with patch("app.services.notification_storage_service.storage.mark_all_as_read") as mock_mark:
                response = await client.post(f"{self.BASE_URL}/read/1234567890")
                assert response.status_code == 200
                assert "marked as read" in response.json()["message"]
                mock_mark.assert_called_once_with("1234567890")

    async def test_clear_notifications(self):
        """POSITIVE: Clear notifications"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            with patch("app.services.notification_storage_service.storage.clear_notifications") as mock_clear:
                response = await client.delete(f"{self.BASE_URL}/1234567890")
                assert response.status_code == 200
                assert "cleared" in response.json()["message"]
                mock_clear.assert_called_with("1234567890")

    async def test_send_notification_invalid_type(self):
        """NEGATIVE: Send notification with invalid type"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"{self.BASE_URL}/send",
                json={
                    "recipient": "1234567890",
                    "message": "Test Message",
                    "type": "INVALID_TYPE"
                }
            )
            # Pydantic validation error or FastAPI 422
            assert response.status_code == 422
