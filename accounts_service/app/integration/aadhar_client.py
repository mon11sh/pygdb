"""
Aadhar Service HTTP Client

HTTP client for communicating with the Aadhar verification service.

Author: GDB Architecture Team
"""

import logging
import httpx
from typing import Dict
from app.config.settings import settings

logger = logging.getLogger(__name__)


class AadharClient:
    """
    HTTP client for Aadhar verification service.
    """
    
    # Aadhar service configuration
    AADHAR_SERVICE_URL = settings.AADHAR_SERVICE_URL
    VERIFY_ENDPOINT = "/api/v1/verify"
    TIMEOUT = 5.0  # seconds
    
    @classmethod
    async def verify_aadhar(cls, aadhar_number: str) -> Dict:
        """
        Verify an Aadhar number with the Aadhar service.
        
        Args:
            aadhar_number: 12-digit Aadhar number to verify
            
        Returns:
            Dictionary with verification response:
            {
                "aadhar_number": str,
                "is_valid": bool,
                "status": str,
                "message": str,
                "timestamp": str
            }
            
        Raises:
            Exception: If Aadhar service is unavailable or returns error
        """
        url = f"{cls.AADHAR_SERVICE_URL}{cls.VERIFY_ENDPOINT}"
        
        logger.info(f"Calling Aadhar service for verification: {aadhar_number[:4]}********")
        
        try:
            async with httpx.AsyncClient(timeout=cls.TIMEOUT) as client:
                response = await client.post(
                    url,
                    json={"aadhar_number": aadhar_number},
                    headers={"X-Internal-API-Key": settings.INTERNAL_API_KEY}
                )
                
                # Check if request was successful
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Aadhar verification response: {result['status']}")
                    return result
                elif response.status_code == 400:
                    # Validation error from Aadhar service
                    error_detail = response.json().get("detail", "Invalid Aadhar format")
                    logger.error(f"Aadhar validation error: {error_detail}")
                    raise ValueError(f"Aadhar validation error: {error_detail}")
                else:
                    # Other errors
                    logger.error(f"Aadhar service returned status {response.status_code}")
                    raise Exception(f"Aadhar service error: HTTP {response.status_code}")
                    
        except httpx.TimeoutException:
            logger.error("Aadhar service request timed out")
            raise Exception("Aadhar verification service is unavailable (timeout)")
        except httpx.ConnectError:
            logger.error("Cannot connect to Aadhar service")
            raise Exception("Aadhar verification service is unavailable (connection refused)")
        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling Aadhar service: {e}")
            raise Exception(f"Aadhar verification service error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error calling Aadhar service: {e}")
            raise
    
    @classmethod
    async def health_check(cls) -> bool:
        """
        Check if Aadhar service is available.
        """
        try:
            async with httpx.AsyncClient(timeout=cls.TIMEOUT) as client:
                response = await client.get(f"{cls.AADHAR_SERVICE_URL}/health")
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Aadhar service health check failed: {e}")
            return False
