"""
Accounts Service - Configuration Settings

This module provides environment-based configuration for the Accounts Service.
Follows 12-factor app principles with environment variables.

Author: GDB Architecture Team
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables.
    """
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    
    # Application Info
    APP_NAME: str = "GDB-Accounts-Service"
    TITLE: str = "GDB Accounts Service"
    DESCRIPTION: str = "Microservice for managing bank accounts"
    APP_VERSION: str = "1.0.0"
    
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8001

    # Hosts accepted by TrustedHostMiddleware (comma-separated). Includes the
    # Docker service name so container-to-container calls (Host: accounts-service)
    # are accepted; override via the ALLOWED_HOSTS env var for other deployments.
    ALLOWED_HOSTS: str = "localhost,127.0.0.1,accounts-service,*.gdb.local"
    
    # ---- Multi-provider database selection -------------------------------
    # Students switch databases by changing ONLY these two values.
    # Supported: sqlite | mysql | postgres | supabase | inmemory
    DATABASE_PROVIDER: str = "postgres"
    # Optional explicit SQLAlchemy URL. Leave EMPTY to auto-build it from the
    # DATABASE_* fields below (postgres/supabase/mysql) or use the sqlite default.
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/gdb_accounts_db"

    # Database Settings (used to build the connection URL for server databases)
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "gdb_accounts_db"
    DATABASE_USER: str = "postgres"
    DATABASE_PASSWORD: str = ""
    MIN_DB_POOL_SIZE: int = 5
    MAX_DB_POOL_SIZE: int = 20
    
    # Security Settings
    PIN_ENCRYPTION_KEY: str = "your-secret-encryption-key"
    JWT_SECRET_KEY: str = "your-super-secret-jwt-key-change-in-production"
    # RS256 public key (PEM) for verifying auth-issued tokens (remediation C-1).
    # Empty => verify legacy HS256 with JWT_SECRET_KEY.
    JWT_PUBLIC_KEY: str = ""

    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DISABLE_AUTH: bool = False
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
    
    # Integration Settings
    ACCOUNT_SERVICE_TIMEOUT: int = 10
    
    # API prefix
    API_PREFIX: str = "/api/v1"
    
    # CORS - Allow frontend origins
    CORS_ALLOWED_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173", "http://localhost:8001", "http://localhost:8002", "http://localhost:8003", "http://localhost:8004"]
    
    # Logging
    LOG_LEVEL: str = "INFO"

    # Compatibility Aliases (Lowercase for existing code)
    @property
    def app_name(self) -> str:
        """Lower-case compatibility alias for APP_NAME."""
        return self.APP_NAME
    @property
    def app_version(self) -> str:
        """Lower-case compatibility alias for APP_VERSION."""
        return self.APP_VERSION
    @property
    def host(self) -> str:
        """Lower-case compatibility alias for HOST."""
        return self.HOST
    @property
    def port(self) -> int:
        """Lower-case compatibility alias for PORT."""
        return self.PORT
    @property
    def database_url(self) -> str:
        """Lower-case compatibility alias for DATABASE_URL."""
        return self.DATABASE_URL
    @property
    def database_provider(self) -> str:
        """Lower-case compatibility alias for DATABASE_PROVIDER."""
        return self.DATABASE_PROVIDER
    @property
    def min_db_pool_size(self) -> int:
        """Lower-case compatibility alias for MIN_DB_POOL_SIZE."""
        return self.MIN_DB_POOL_SIZE
    @property
    def max_db_pool_size(self) -> int:
        """Lower-case compatibility alias for MAX_DB_POOL_SIZE."""
        return self.MAX_DB_POOL_SIZE
    @property
    def jwt_secret_key(self) -> str:
        """Lower-case compatibility alias for JWT_SECRET_KEY."""
        return self.JWT_SECRET_KEY
    @property
    def jwt_algorithm(self) -> str:
        """Lower-case compatibility alias for JWT_ALGORITHM."""
        return self.JWT_ALGORITHM
    @property
    def api_prefix(self) -> str:
        """Lower-case compatibility alias for API_PREFIX."""
        return self.API_PREFIX
    @property
    def log_level(self) -> str:
        """Lower-case compatibility alias for LOG_LEVEL."""
        return self.LOG_LEVEL
    @property
    def environment(self) -> str:
        """Lower-case compatibility alias for ENVIRONMENT."""
        return self.ENVIRONMENT
    @property
    def debug(self) -> bool:
        """Lower-case compatibility alias for DEBUG."""
        return self.DEBUG
    @property
    def disable_auth(self) -> bool:
        """Lower-case compatibility alias for DISABLE_AUTH."""
        return self.DISABLE_AUTH
    @property
    def account_service_url(self) -> str:
        """Lower-case compatibility alias for ACCOUNTS_SERVICE_URL."""
        return self.ACCOUNTS_SERVICE_URL
    @property
    def internal_api_key(self) -> str:
        """Lower-case compatibility alias for INTERNAL_API_KEY."""
        return self.INTERNAL_API_KEY

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
