"""
Account Service Client

Handles all communication with Account Service.
CRITICAL: Every withdrawal, deposit, and transfer MUST validate via Account Service.
"""

import httpx
import logging
from typing import Optional, Dict, Any
from app.config.settings import settings
from app.correlation import current_correlation_id
from gdb_common.resilience import CircuitBreaker, CircuitBreakerOpen
from app.exceptions.transaction_exceptions import (
    AccountNotFoundException,
    AccountNotActiveException,
    InvalidPINException,
    ServiceUnavailableException,
    AccountServiceException,
)

logger = logging.getLogger(__name__)

# Circuit breaker for the Account Service dependency: after repeated failures it
# OPENs and fails fast for a cooldown instead of piling onto a struggling service.
_account_breaker = CircuitBreaker("accounts-service", failure_threshold=5, reset_timeout=30.0)


class AccountServiceClient:
    """Client for Account Service communication."""

    def __init__(self):
        """Initialize Account Service client."""
        self.base_url = settings.ACCOUNTS_SERVICE_URL
        self.timeout = settings.ACCOUNT_SERVICE_TIMEOUT

    async def validate_account(self, account_number: int) -> Dict[str, Any]:
        """
        Validate account exists and is active using INTERNAL API.
        
        MANDATORY CALL before any transaction operation.
        Uses service-to-service internal endpoint.
        
        Args:
            account_number: Account to validate
            
        Returns:
            Account details dict with keys:
            - account_number
            - is_active
            - balance
            - privilege (PREMIUM/GOLD/SILVER)
            
        Raises:
            AccountNotFoundException: If account doesn't exist
            AccountNotActiveException: If account is not active
            ServiceUnavailableException: If Account Service is down
        """
        endpoint = f"{self.base_url}/api/v1/internal/accounts/{account_number}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Route the downstream call through the circuit breaker.
                response = await _account_breaker.call(
                    lambda: client.get(
                        endpoint,
                        headers={"X-Internal-API-Key": settings.INTERNAL_API_KEY, "X-Correlation-ID": current_correlation_id()},
                    )
                )

                if response.status_code == 404:
                    raise AccountNotFoundException(f"Account {account_number} not found")

                if response.status_code == 200:
                    data = response.json()
                    if not data.get("is_active", False):
                        raise AccountNotActiveException(f"Account {account_number} is not active")
                    return data
                
                raise AccountServiceException(f"Account Service error: {response.text}")
                
        except CircuitBreakerOpen:
            logger.warning("Account Service circuit breaker OPEN — failing fast")
            raise ServiceUnavailableException("Account Service temporarily unavailable (circuit open)")
        except httpx.HTTPError as e:
            logger.error(f"Account Service connection error: {str(e)}")
            raise ServiceUnavailableException("Account Service is currently unavailable")

    async def verify_pin(self, account_number: int, pin: str) -> bool:
        """
        Verify account PIN using INTERNAL API.
        
        MANDATORY for withdraw and transfer operations.
        Uses service-to-service internal endpoint.
        
        Args:
            account_number: Account number
            pin: PIN to verify
            
        Returns:
            True if PIN is valid
            
        Raises:
            InvalidPINException: If PIN is invalid
            AccountNotFoundException: If account doesn't exist
            ServiceUnavailableException: If Account Service is down
        """
        endpoint = f"{self.base_url}/api/v1/internal/accounts/{account_number}/verify-pin"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    endpoint,
                    params={"pin": pin},
                    headers={"X-Internal-API-Key": settings.INTERNAL_API_KEY, "X-Correlation-ID": current_correlation_id()},
                )
                
                if response.status_code == 404:
                    raise AccountNotFoundException(f"Account {account_number} not found")
                
                if response.status_code == 401:
                    raise InvalidPINException("Invalid PIN provided")
                
                if response.status_code == 200:
                    data = response.json()
                    # Enforce the result: a 200 with pin_valid=false is still a
                    # wrong PIN. Never return a falsey result to callers who only
                    # await this — always raise so a bad PIN blocks the operation.
                    if not data.get("pin_valid", False):
                        raise InvalidPINException("Invalid PIN provided")
                    return True

                raise AccountServiceException(f"PIN verification failed: {response.text}")
                
        except httpx.HTTPError:
            raise ServiceUnavailableException("Account Service is unavailable")

    async def debit_account(
        self,
        account_number: int,
        amount: float,
        description: str = "Transaction"
    ) -> Dict[str, Any]:
        """
        Debit amount from account (for withdrawal/transfer) using INTERNAL API.
        
        Args:
            account_number: Account to debit
            amount: Amount to debit
            description: Transaction description
            
        Returns:
            Account data after debit with key 'new_balance'
            
        Raises:
            InsufficientFundsException: If not enough balance
            ServiceUnavailableException: If Account Service is down
        """
        endpoint = f"{self.base_url}/api/v1/internal/accounts/{account_number}/debit"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {"amount": amount, "description": description}
                response = await client.post(
                    endpoint,
                    params=params,
                    headers={"X-Internal-API-Key": settings.INTERNAL_API_KEY, "X-Correlation-ID": current_correlation_id()},
                )
                
                if response.status_code == 200:
                    return response.json()
                
                if response.status_code == 400:
                    error_data = response.json()
                    raise AccountServiceException(error_data.get("error"))
                
                raise ServiceUnavailableException("Debit operation failed")
                
        except httpx.HTTPError:
            raise ServiceUnavailableException("Account Service is unavailable")

    async def credit_account(
        self,
        account_number: int,
        amount: float,
        description: str = "Transaction"
    ) -> Dict[str, Any]:
        """
        Credit amount to account (for deposit/transfer) using INTERNAL API.
        
        Args:
            account_number: Account to credit
            amount: Amount to credit
            description: Transaction description
            
        Returns:
            Account data after credit with key 'new_balance'
            
        Raises:
            ServiceUnavailableException: If Account Service is down
        """
        endpoint = f"{self.base_url}/api/v1/internal/accounts/{account_number}/credit"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {"amount": amount, "description": description}
                response = await client.post(
                    endpoint,
                    params=params,
                    headers={"X-Internal-API-Key": settings.INTERNAL_API_KEY, "X-Correlation-ID": current_correlation_id()},
                )
                
                if response.status_code == 200:
                    return response.json()
                
                raise ServiceUnavailableException("Credit operation failed")
                
        except httpx.HTTPError:
            raise ServiceUnavailableException("Account Service is unavailable")

    async def get_account_privilege(self, account_number: int) -> str:
        """
        Get account privilege level using INTERNAL API.
        
        Args:
            account_number: Account number
            
        Returns:
            Privilege level (PREMIUM/GOLD/SILVER)
        """
        endpoint = f"{self.base_url}/api/v1/internal/accounts/{account_number}/privilege"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    endpoint,
                    headers={"X-Internal-API-Key": settings.INTERNAL_API_KEY, "X-Correlation-ID": current_correlation_id()},
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("privilege", "SILVER")
                
                raise ServiceUnavailableException("Could not fetch account privilege")
                
        except httpx.HTTPError:
            raise ServiceUnavailableException("Account Service is unavailable")


# Singleton instance
account_service_client = AccountServiceClient()
