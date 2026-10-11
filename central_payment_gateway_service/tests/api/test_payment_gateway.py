import pytest
import asyncio
from unittest.mock import patch, MagicMock
from app.main import app
from httpx import ASGITransport, AsyncClient

@pytest.mark.asyncio
class TestPaymentGatewayService:
    """Test suite for Central Payment Gateway Service"""

    BASE_URL = "/api/v1/payment"

    async def test_health_check(self):
        """POSITIVE: Health check returns 200"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "active"

    async def test_process_payment_success(self):
        """POSITIVE: Process a valid payment"""
        payload = {
            "source_account_id": 123,
            "destination_account_id": 456,
            "amount": 100.0,
            "mode": "IMPS",
            "reference_id": "REF789"
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Patch sleep to avoid delay
            with patch("asyncio.sleep", return_value=None):
                # Patch random to avoid failure
                with patch("random.random", return_value=0.5):
                    response = await client.post(f"{self.BASE_URL}/process", json=payload)
                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] == True
                    assert data["transaction_id"] == "REF789"
                    assert "gateway_ref_id" in data

    async def test_process_payment_invalid_amount(self):
        """NEGATIVE: Payment with zero amount - should fail Pydantic validation (422)"""
        payload = {
            "source_account_id": 123,
            "destination_account_id": 456,
            "amount": 0.0,
            "mode": "IMPS"
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(f"{self.BASE_URL}/process", json=payload)
            # amount has Field(..., gt=0), so 0.0 results in 422
            assert response.status_code == 422

    async def test_process_payment_same_account(self):
        """NEGATIVE: Source and destination accounts are same"""
        payload = {
            "source_account_id": 123,
            "destination_account_id": 123,
            "amount": 100.0,
            "mode": "IMPS"
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            with patch("asyncio.sleep", return_value=None):
                response = await client.post(f"{self.BASE_URL}/process", json=payload)
                assert response.status_code == 200
                assert response.json()["success"] == False
                assert "same" in response.json()["message"]

    async def test_process_payment_random_failure(self):
        """EDGE: Simulate random gateway failure"""
        payload = {
            "source_account_id": 123,
            "destination_account_id": 456,
            "amount": 100.0,
            "mode": "IMPS"
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            with patch("asyncio.sleep", return_value=None):
                # Set random.random to return 0.005 which is < 0.01
                with patch("random.random", return_value=0.005):
                    response = await client.post(f"{self.BASE_URL}/process", json=payload)
                    assert response.status_code == 200
                    assert response.json()["success"] == False
                    assert "Gateway Error" in response.json()["message"]
