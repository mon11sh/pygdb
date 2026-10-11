"""
Authentication Audit Log Repository — provider-agnostic data-access CONTRACT.

Records all authentication attempts for security auditing. Like the token
repository, this is a thin interface: every method forwards to the concrete
repository owned by the ACTIVE database provider (settings.DATABASE_PROVIDER).

Concrete implementations live in:
  - repositories.sqlalchemy_repositories.SqlAlchemyAuthAuditRepository
        -> sqlite / mysql / postgres / supabase
  - repositories.inmemory_repositories.InMemoryAuthAuditRepository
        -> inmemory

Module path, class name, static method signatures and return shapes are kept
UNCHANGED so services and tests that import / patch
`AuthAuditRepository.<method>` keep working exactly as before.

Author: GDB Architecture Team
"""

import logging
from abc import ABC
from typing import Optional, List

from app.models.auth_models import AuthAuditLog


logger = logging.getLogger(__name__)


def _repo():
    """Return the active AuthAuditRepository implementation from the provider."""
    from app.database.connection import get_provider
    return get_provider().audit_repository()


class AuthAuditRepository(ABC):
    """Abstract, database-agnostic repository for auth_audit_logs."""

    @staticmethod
    async def log_login_attempt(
        login_id: str,
        user_id: Optional[str],
        action: str,  # LOGIN_SUCCESS, LOGIN_FAILURE
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> str:
        """Log a login attempt. Returns the audit log ID (UUID string)."""
        return await _repo().log_login_attempt(
            login_id, user_id, action, reason, ip_address, user_agent
        )

    @staticmethod
    async def log_login_success(
        login_id: str,
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> str:
        """Log a successful login. Returns the audit log ID."""
        return await _repo().log_login_success(
            login_id, user_id, ip_address, user_agent
        )

    @staticmethod
    async def log_login_failure(
        login_id: str,
        user_id: Optional[str],
        reason: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> str:
        """Log a failed login attempt. Returns the audit log ID."""
        return await _repo().log_login_failure(
            login_id, user_id, reason, ip_address, user_agent
        )

    @staticmethod
    async def get_audit_log(log_id: str) -> Optional[AuthAuditLog]:
        """Retrieve an audit log entry by ID. Returns an AuthAuditLog or None."""
        return await _repo().get_audit_log(log_id)

    @staticmethod
    async def get_user_audit_logs(
        user_id: str,
        limit: int = 100,
    ) -> List[AuthAuditLog]:
        """Return recent audit logs for a user (newest first)."""
        return await _repo().get_user_audit_logs(user_id, limit)

    @staticmethod
    async def get_login_id_audit_logs(
        login_id: str,
        limit: int = 100,
    ) -> List[AuthAuditLog]:
        """Return recent audit logs for a login ID (newest first)."""
        return await _repo().get_login_id_audit_logs(login_id, limit)
