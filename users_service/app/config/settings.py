"""
User Management Service - Configuration Settings

This module provides environment-based configuration for the User Management Service.
Follows 12-factor app principles with environment variables.
"""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    User Management Service Configuration
    """
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    
    # Service Info
    SERVICE_NAME: str = "GDB-User-Service"
    TITLE: str = "GDB User Management Service"
    DESCRIPTION: str = "FastAPI service for user management with role-based access control"
    SERVICE_VERSION: str = "1.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8003
    
    # ---- Multi-provider database selection -------------------------------
    # Students switch databases by changing ONLY these two values.
    # Supported: sqlite | mysql | postgres | supabase | inmemory
    DATABASE_PROVIDER: str = "postgres"
    # Optional explicit SQLAlchemy URL. Leave empty to auto-build it from the
    # DATABASE_* fields below (postgres/supabase/mysql) or use the sqlite default.
    DATABASE_URL: str = ""

    # Database Settings (used to build the connection URL for server databases)
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "gdb_users_db"
    DATABASE_USER: str = "postgres"
    DATABASE_PASSWORD: str = ""
    
    # Security Settings
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    
    # JWT Settings (SHARED)
    JWT_SECRET_KEY: str = "your-super-secret-jwt-key-change-in-production"
    # RS256 public key (PEM) for verifying auth-issued tokens (remediation C-1).
    # Empty => verify legacy HS256 with JWT_SECRET_KEY.
    JWT_PUBLIC_KEY: str = ""

    JWT_ALGORITHM: str = "HS256"

    # Inter-Service Authentication (SHARED internal API key)
    INTERNAL_API_KEY: str = "dev-internal-api-key-change-in-prod"
    
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
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = "logs/users_service.log"
    
    # CORS Settings
    CORS_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: List[str] = ["*"]
    CORS_HEADERS: List[str] = ["*"]
    
    # API prefix
    API_PREFIX: str = "/api/v1"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )


# Load settings from environment
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
