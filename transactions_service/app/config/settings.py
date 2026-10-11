"""
Configuration Module for Transaction Service

Handles:
- Database connection settings
- Account Service URL
- JWT configuration
- Logging paths
- Service ports
"""

import os
from typing import Optional, Dict, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    """
    Transaction Service Configuration
    """
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    
    # Service Info
    SERVICE_NAME: str = "GDB-Transaction-Service"
    SERVICE_VERSION: str = "1.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8002
    
    # ---- Multi-provider database selection -------------------------------
    # Students switch databases by changing ONLY these two values.
    # Supported: sqlite | mysql | postgres | supabase | inmemory
    DATABASE_PROVIDER: str = "postgres"
    # Optional explicit SQLAlchemy URL. Leave empty to auto-build it from the
    # DB_* fields below (postgres/supabase/mysql) or use the sqlite default.
    DATABASE_URL: str = ""

    # Database Settings (used to build the connection URL for server databases)
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "password"
    DB_NAME: str = "gdb_transactions_db"
    DB_POOL_MIN_SIZE: int = 5
    DB_POOL_MAX_SIZE: int = 20
    DB_TIMEOUT: int = 30

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
    
    # Compatibility lower-case properties
    @property
    def app_host(self) -> str:
        """Lower-case compatibility alias for the configured service HOST."""
        return self.HOST
    @property
    def app_port(self) -> int:
        """Lower-case compatibility alias for the configured service PORT."""
        return self.PORT
    @property
    def debug(self) -> bool:
        """Lower-case compatibility alias for the DEBUG flag."""
        return self.DEBUG
    @property
    def app_name(self) -> str:
        """Lower-case compatibility alias for the SERVICE_NAME."""
        return self.SERVICE_NAME

    # Timeouts
    ACCOUNT_SERVICE_TIMEOUT: int = 10

    # JWT & Security
    JWT_SECRET_KEY: str = "your-super-secret-jwt-key-change-in-production"
    # RS256 public key (PEM) for verifying auth-issued tokens (remediation C-1).
    # Empty => verify legacy HS256 with JWT_SECRET_KEY.
    JWT_PUBLIC_KEY: str = ""

    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # Inter-Service Authentication
    INTERNAL_API_KEY: str = "dev-internal-api-key-change-in-prod"
    
    # RBAC Roles
    ALLOWED_ROLES: Dict[str, List[str]] = {
        "WITHDRAW": ["MANAGER", "TELLER"],
        "DEPOSIT": ["MANAGER", "TELLER"],
        "TRANSFER": ["MANAGER", "TELLER"],
        "VIEW_LOGS": ["ADMIN"],
        "MANAGE_LIMITS": ["ADMIN"],
    }

    # Transfer Limits
    # per_transaction_limit is the fallback used only when the DB transfer_limits
    # table has no row for the privilege; the DB value is preferred.
    TRANSFER_LIMITS: Dict[str, Dict[str, float]] = {
        "PREMIUM": {"daily_limit": 100000.0, "daily_transaction_count": 50, "per_transaction_limit": 100000.0},
        "GOLD": {"daily_limit": 50000.0, "daily_transaction_count": 25, "per_transaction_limit": 50000.0},
        "SILVER": {"daily_limit": 25000.0, "daily_transaction_count": 10, "per_transaction_limit": 25000.0},
        "BASIC": {"daily_limit": 10000.0, "daily_transaction_count": 5, "per_transaction_limit": 10000.0},
    }

    # Logging
    LOG_DIR: str = "./logs/transactions"
    LOG_FILE_FORMAT: str = "%Y-%m-%d"
    LOG_LEVEL: str = "INFO"

    # Business Rules
    MINIMUM_DEPOSIT_AMOUNT: float = 1.00
    MINIMUM_WITHDRAWAL_AMOUNT: float = 1.00
    MINIMUM_TRANSFER_AMOUNT: float = 1.00
    MAXIMUM_TRANSACTION_AMOUNT: float = 999999999.99
    PIN_LENGTH: int = 4
    MAX_PIN_ATTEMPTS: int = 3

    # API Prefix
    API_VERSION: str = "v1"
    API_BASE_URL: str = f"/api/{API_VERSION}"
    
    # CORS
    CORS_ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Idempotency
    IDEMPOTENCY_HEADER_NAME: str = "Idempotency-Key"
    IDEMPOTENCY_TTL_HOURS: int = 24

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )

    def ensure_log_dir(self) -> None:
        """Create the configured transaction log directory if it does not exist."""
        if not os.path.exists(self.LOG_DIR):
            os.makedirs(self.LOG_DIR, exist_ok=True)

settings = Settings()
settings.ensure_log_dir()


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
