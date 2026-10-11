import pytest
from app.main import app
from httpx import ASGITransport, AsyncClient
from app.services.aadhar_verification_service import AadharVerificationService

@pytest.mark.asyncio
class TestAadharService:
    """Test suite for Aadhar Verification Service"""

    BASE_URL = "/api/v1"

    async def test_health_check(self):
        """POSITIVE: Health check returns 200"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"

    async def test_verify_valid_aadhar(self):
        """POSITIVE: Verify a valid Aadhar number"""
        valid_aadhar = list(AadharVerificationService.AADHAR_DATABASE.keys())[0]
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"{self.BASE_URL}/verify",
                json={"aadhar_number": valid_aadhar}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["is_valid"] == True
            assert data["status"] == "VERIFIED"
            assert "name" in data
            assert data["aadhar_number"] == valid_aadhar

    async def test_verify_invalid_aadhar(self):
        """NEGATIVE: Verify an invalid Aadhar number"""
        invalid_aadhar = "000000000000"
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"{self.BASE_URL}/verify",
                json={"aadhar_number": invalid_aadhar}
            )
            assert response.status_code == 200
            assert response.json()["is_valid"] == False
            assert response.json()["status"] == "INVALID"

    async def test_get_valid_aadhars(self):
        """POSITIVE: Get list of valid Aadhar numbers"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"{self.BASE_URL}/valid-numbers")
            assert response.status_code == 200
            assert "valid_aadhar_numbers" in response.json()
            assert response.json()["count"] == len(AadharVerificationService.AADHAR_DATABASE)

    async def test_verify_bad_format(self):
        """NEGATIVE: Verification with malformed Aadhar number"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Aadhar must be 12 digits. Let's send short one.
            response = await client.post(
                f"{self.BASE_URL}/verify",
                json={"aadhar_number": "123"}
            )
            # Depending on Pydantic validation it might be 400 or 422
            assert response.status_code in [400, 422]
