"""
Audit Service - Business logic for audit logging.

Delegates persistence to the active database provider's AuditRepository, so the
audit trail follows whichever database the student selected
(sqlite/mysql/postgres/supabase/inmemory). Best-effort: a logging failure never
breaks the main user-management operation.
"""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class AuditService:
    """Service for audit logging."""

    @staticmethod
    async def log_action(
        user_id: int,
        action: str,
        old_data: Optional[Dict[str, Any]] = None,
        new_data: Optional[Dict[str, Any]] = None,
        performed_by: Optional[str] = None,
    ) -> bool:
        """
        Log an audit action via the active provider's audit repository.

        Returns True on success, False otherwise (never raises).
        """
        try:
            from ..database.connection import get_provider
            repo = get_provider().audit_repository()
            return await repo.log_action(
                user_id=user_id,
                action=action,
                old_data=old_data,
                new_data=new_data,
                performed_by=performed_by,
            )
        except Exception as e:
            logger.error(f"❌ Error logging audit action: {str(e)}")
            # Don't raise - audit logging shouldn't break the main operation
            return False
