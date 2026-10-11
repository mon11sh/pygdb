"""
In-memory repository implementations (DATABASE_PROVIDER=inmemory).

Pure Python dicts — no SQL engine, no external driver. Data lives only for the
process lifetime. Implements the same UserRepository / AuditRepository contracts
as the SQL implementations, so services never know the difference.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

import bcrypt

from .user_repository import UserRepository
from .audit_repository import AuditRepository

logger = logging.getLogger(__name__)


class InMemoryStore:
    """Process-lifetime store shared by the in-memory repositories."""

    def __init__(self):
        """Initialize empty user/audit collections and the id sequence."""
        self.users: Dict[int, Dict[str, Any]] = {}
        self.audit: List[Dict[str, Any]] = []
        self._seq = 0

    def next_user_id(self) -> int:
        """Return the next monotonically increasing user id."""
        self._seq += 1
        return self._seq


def _hash(password: str) -> str:
    """Hash a plaintext password with bcrypt and return the hash as str."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _without_password(row: Dict[str, Any]) -> Dict[str, Any]:
    """Return a shallow copy of a user row with the password field removed."""
    return {k: v for k, v in row.items() if k != "password"}


class InMemoryUserRepository(UserRepository):
    """In-memory UserRepository backed by the shared InMemoryStore."""

    def __init__(self, store: InMemoryStore):
        """Bind this repository to the given process-lifetime store."""
        self._store = store

    async def create_user(self, username, login_id, password, role="MANAGER"):
        """Create a user (enforcing unique login_id). Returns it WITHOUT the
        password field.

        Raises:
            ValueError: If the login_id already exists.
        """
        # Mirror the DB UNIQUE(login_id) constraint.
        if any(r["login_id"] == login_id for r in self._store.users.values()):
            raise ValueError(f"login_id already exists: {login_id}")
        uid = self._store.next_user_id()
        now = datetime.utcnow()
        row = {
            "user_id": uid, "username": username, "login_id": login_id,
            "password": _hash(password), "role": role, "is_active": True,
            "created_at": now, "updated_at": now,
        }
        self._store.users[uid] = row
        logger.info(f"✅ User created: {login_id}")
        return _without_password(row)

    async def get_user_by_login_id(self, login_id):
        """Return the user (INCLUDING the password hash) matching login_id, or None."""
        for row in self._store.users.values():
            if row["login_id"] == login_id:
                return dict(row)  # includes password
        return None

    async def get_user_by_id(self, user_id):
        """Return the user (INCLUDING the password hash) matching user_id, or None."""
        row = self._store.users.get(user_id)
        return dict(row) if row else None  # includes password

    async def update_user(self, user_id, username=None, password=None, role=None):
        """Update the provided fields (password re-hashed if given). Returns the
        updated user INCLUDING the password hash, or None if not found."""
        row = self._store.users.get(user_id)
        if not row:
            return None
        if username:
            row["username"] = username
        if password:
            row["password"] = _hash(password)
        if role:
            row["role"] = role
        row["updated_at"] = datetime.utcnow()
        return dict(row)  # includes password

    async def inactivate_user(self, user_id):
        """Set is_active=False. Returns the user WITHOUT the password field, or None."""
        row = self._store.users.get(user_id)
        if not row:
            return None
        row["is_active"] = False
        row["updated_at"] = datetime.utcnow()
        return _without_password(row)

    async def activate_user(self, user_id):
        """Set is_active=True. Returns the user WITHOUT the password field, or None."""
        row = self._store.users.get(user_id)
        if not row:
            return None
        row["is_active"] = True
        row["updated_at"] = datetime.utcnow()
        return _without_password(row)

    async def count_active_admins(self):
        """Return the number of currently active ADMIN users."""
        return sum(
            1 for r in self._store.users.values()
            if r["role"] == "ADMIN" and r["is_active"]
        )

    async def get_all_users(self):
        """Return all users (WITHOUT password), newest first."""
        rows = sorted(
            self._store.users.values(), key=lambda r: r["created_at"], reverse=True
        )
        return [_without_password(r) for r in rows]


class InMemoryAuditRepository(AuditRepository):
    """In-memory AuditRepository backed by the shared InMemoryStore."""

    def __init__(self, store: InMemoryStore):
        """Bind this audit repository to the given process-lifetime store."""
        self._store = store

    async def log_action(self, user_id, action, old_data=None, new_data=None, performed_by=None):
        """Append an audit entry to the store. Returns True on success, False on
        failure (best-effort; never raises)."""
        try:
            self._store.audit.append({
                "log_id": len(self._store.audit) + 1,
                "user_id": user_id, "action": action,
                "old_data": old_data, "new_data": new_data,
                "performed_by": performed_by, "timestamp": datetime.utcnow(),
            })
            logger.info(f"✅ Audit logged: {action} for user_id {user_id}")
            return True
        except Exception as e:  # pragma: no cover - best effort
            logger.error(f"❌ Error logging audit action: {e}")
            return False
