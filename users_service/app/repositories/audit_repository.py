"""
Audit Repository — provider-agnostic contract for the user audit trail.

Concrete implementations live alongside the user-repository implementations
(inmemory_repositories / sqlalchemy_repositories) and are selected by the same
database provider, so the audit log follows whichever database the student picks.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class AuditRepository(ABC):
    """Abstract, database-agnostic repository for user-management audit logs."""

    @abstractmethod
    async def log_action(
        self,
        user_id: Optional[int],
        action: str,
        old_data: Optional[Dict[str, Any]] = None,
        new_data: Optional[Dict[str, Any]] = None,
        performed_by: Optional[str] = None,
    ) -> bool:
        """Persist an audit entry. Best-effort: returns True on success, False on
        failure (auditing must never break the main operation)."""
