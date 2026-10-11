"""
Company Verification Client

Client for communicating with the external Company Registration Validation (CRV) service.

Author: GDB Architecture Team
"""

import httpx
import logging
from typing import Dict, Any
from app.config.settings import settings

logger = logging.getLogger(__name__)


class CompanyClient:
    """
    HTTP client for Company CRV service.
    """
    
    # Service configuration
    SERVICE_URL = settings.COMPANY_SERVICE_URL
    VERIFY_ENDPOINT = "/api/v1/company/verify"
    TIMEOUT = 5.0  # seconds
    
    @classmethod
    async def verify_registration(cls, registration_number: str) -> Dict[str, Any]:
        """
        Verify a company registration number with the CRV service.
        
        Args:
            registration_number: 21-character CIN to verify
            
        Returns:
            Dictionary with verification response:
            {
                "registration_number": str,
                "is_valid": bool,
                "status": str,
                "message": str,
                "timestamp": str
            }
            
        Raises:
            Exception: If CRV service is unavailable or returns error
        """
        url = f"{cls.SERVICE_URL}{cls.VERIFY_ENDPOINT}"
        
        logger.info(f"Calling Company CRV service for verification: {registration_number[:8]}*************")
        
        try:
            async with httpx.AsyncClient(timeout=cls.TIMEOUT) as client:
                response = await client.post(
                    url,
                    json={"registration_number": registration_number},
                    headers={"X-Internal-API-Key": settings.INTERNAL_API_KEY}
                )
                
                # Check if request was successful
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Company verification response: {result['status']}")
                    return result
                elif response.status_code == 400:
                    # Validation error from service
                    error_detail = response.json().get("detail", "Invalid registration number format")
                    logger.error(f"Company validation error: {error_detail}")
                    raise ValueError(f"Company validation error: {error_detail}")
                else:
                    # Other errors
                    logger.error(f"Company CRV service returned status {response.status_code}")
                    raise Exception(f"Company CRV service error: HTTP {response.status_code}")
                    
        except httpx.TimeoutException:
            logger.error("Company CRV service request timed out")
            raise Exception("Company verification service is unavailable (timeout)")
        except httpx.ConnectError:
            logger.error("Cannot connect to Company CRV service")
            raise Exception("Company verification service is unavailable (connection refused)")
        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling Company CRV service: {e}")
            raise Exception(f"Company verification service error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error calling Company CRV service: {e}")
            raise

    @classmethod
    async def health_check(cls) -> bool:
        """
        Check if Company CRV service is reachable.
        """
        url = f"{cls.SERVICE_URL}/health"
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(url)
                return response.status_code == 200
        except Exception:
            return False
