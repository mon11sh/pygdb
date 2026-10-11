"""HTTP client for the central Payment Gateway service.

Wraps the async call used during transfers to obtain a second-level payment
validation/authorization from the payment gateway. Connection or non-200
responses resolve to a safe `False` so a gateway failure blocks the transfer
rather than allowing an unvalidated money movement.
"""

import httpx
import logging
from typing import Optional
from app.config.settings import settings
from app.correlation import current_correlation_id

logger = logging.getLogger(__name__)

class PaymentGatewayClient:
    """Async client that validates payments against the central Payment Gateway."""

    @property
    def BASE_URL(self):
        """Base URL of the Payment Gateway payment API, from settings."""
        return f"{settings.PAYMENT_GATEWAY_SERVICE_URL}/api/v1/payment"

    async def validate_payment(
        self, 
        source_account: int, 
        dest_account: int, 
        amount: float, 
        mode: str
    ) -> bool:
        """
        Call Central Payment Gateway for 2nd Level Validation.
        """
        try:
            payload = {
                "source_account_id": source_account,
                "destination_account_id": dest_account,
                "amount": amount,
                "mode": mode,
                "reference_id": None
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/process",
                    json=payload,
                    headers={"X-Internal-API-Key": settings.INTERNAL_API_KEY, "X-Correlation-ID": current_correlation_id()},
                    timeout=5.0,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("success", False)
                else:
                    logger.error(f"Payment Gateway Error: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Payment Gateway Connection Failed: {str(e)}")
            return False

payment_gateway_client = PaymentGatewayClient()
