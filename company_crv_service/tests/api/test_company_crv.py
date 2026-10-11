import pytest
from app.main import app
from httpx import ASGITransport, AsyncClient
from app.services.company_verification_service import CompanyVerificationService

@pytest.mark.asyncio
class TestCompanyCRVService:
    """Test suite for Company Verification Service"""

    BASE_URL = "/api/v1"

    async def test_health_check(self):
        """POSITIVE: Health check returns 200"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"

    async def test_verify_valid_company(self):
        """POSITIVE: Verify a valid registration number"""
        valid_cin = list(CompanyVerificationService.VALID_REGISTRATION_NUMBERS)[0]
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"{self.BASE_URL}/company/verify",
                json={"registration_number": valid_cin}
            )
            assert response.status_code == 200
            assert response.json()["is_valid"] == True
            assert response.json()["status"] == "VERIFIED"

    async def test_verify_invalid_company(self):
        """NEGATIVE: Verify an invalid registration number"""
        invalid_cin = "INVALID12345678901234"
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"{self.BASE_URL}/company/verify",
                json={"registration_number": invalid_cin}
            )
            assert response.status_code == 200
            assert response.json()["is_valid"] == False
            assert response.json()["status"] == "INVALID"

    async def test_get_valid_companies(self):
        """POSITIVE: Get list of valid registration numbers"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"{self.BASE_URL}/company/valid-companies")
            assert response.status_code == 200
            assert "valid_companies" in response.json()
            assert response.json()["count"] == len(CompanyVerificationService.VALID_REGISTRATION_NUMBERS)

    async def test_verify_missing_payload(self):
        """NEGATIVE: Missing payload"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(f"{self.BASE_URL}/company/verify", json={})
            assert response.status_code == 422
