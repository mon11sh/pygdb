"""Application configuration for the Central Payment Gateway service.

Defines the :class:`Settings` model (loaded from environment variables and an
optional ``.env`` file via ``pydantic-settings``) and exposes a shared
``settings`` singleton. Also performs a fail-fast security assertion at import
time to refuse start-up when production is configured with default/empty
shared secrets.
"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Central Payment Gateway Service Configuration
    """
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    
    # Service Info
    APP_NAME: str = "GDB-Payment-Gateway-Service"
    TITLE: str = "GDB Central Payment Gateway Service"
    DESCRIPTION: str = "Simulated Third-Party Payment Gateway for GDB Ecosystem"
    APP_VERSION: str = "1.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8008
    
    # Inter-Service URLs (StandardizedPlural and LegacySingular)
    ACCOUNTS_SERVICE_URL: str = "http://localhost:8001"
    ACCOUNT_SERVICE_URL: str = "http://localhost:8001"
    
    TRANSACTIONS_SERVICE_URL: str = "http://localhost:8002"
    TRANSACTION_SERVICE_URL: str = "http://localhost:8002"
    
    USERS_SERVICE_URL: str = "http://localhost:8003"
    USER_SERVICE_URL: str = "http://localhost:8003"
    
    AUTH_SERVICE_URL: str = "http://localhost:8004"
    AADHAR_SERVICE_URL: str = "http://localhost:8005"
    COMPANY_SERVICE_URL: str = "http://localhost:8006"
    NOTIFICATION_SERVICE_URL: str = "http://localhost:8007"
    PAYMENT_GATEWAY_SERVICE_URL: str = "http://localhost:8008"
    
    # Inter-Service Authentication
    INTERNAL_API_KEY: str = "dev-internal-api-key-change-in-prod"

    # CORS
    CORS_ALLOWED_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )

settings = Settings()


# --- Enterprise remediation (C-1/C-2): fail-fast on insecure production config ---
def _assert_secure_config() -> None:
    """Refuse to start in production with default/empty shared secrets."""
    if str(getattr(settings, "ENVIRONMENT", "development")).lower() != "production":
        return
    if settings.INTERNAL_API_KEY in ("", None, "dev-internal-api-key-change-in-prod"):
        raise RuntimeError("INTERNAL_API_KEY is unset/default in production; inject a real secret.")
    _jwt = getattr(settings, "JWT_SECRET_KEY", None)
    if _jwt is not None and (not _jwt or "change-in-production" in _jwt or "do-not-use" in _jwt):
        raise RuntimeError("JWT_SECRET_KEY is unset/default in production; inject a real secret.")


_assert_secure_config()
