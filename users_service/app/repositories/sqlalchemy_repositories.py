"""
SQLAlchemy repository implementations — one code path that runs on every SQL
provider: sqlite / mysql / postgres / supabase. The active engine/session is
supplied by the SQLAlchemy database provider; the SQL below is dialect-neutral
(no Postgres-only $n / RETURNING / nextval / ON CONFLICT).

Imported ONLY when a SQL provider is selected, so non-SQL setups never load
SQLAlchemy.
"""

import json
import logging
from typing import Optional, Dict, Any, List

import bcrypt
from sqlalchemy import select, func

from .user_repository import UserRepository
from .audit_repository import AuditRepository
from ..database.orm_models import UserORM, AuditLogORM, user_to_dict

logger = logging.getLogger(__name__)


def _hash(password: str) -> str:
    """Hash a plaintext password with bcrypt and return the hash as str."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


class SqlAlchemyUserRepository(UserRepository):
    """UserRepository implementation over a SQLAlchemy async session factory."""

    def __init__(self, session_factory):
        """Store the async session factory bound to the active engine."""
        # session_factory: async_sessionmaker bound to the active engine.
        self._session_factory = session_factory

    async def create_user(self, username, login_id, password, role="MANAGER"):
        """Insert a new user (password hashed). Returns it WITHOUT the password field."""
        async with self._session_factory() as session:
            user = UserORM(
                username=username, login_id=login_id,
                password=_hash(password), role=role, is_active=True,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            logger.info(f"✅ User created: {login_id}")
            return user_to_dict(user, include_password=False)

    async def get_user_by_login_id(self, login_id):
        """Return the user (INCLUDING the password hash) matching login_id, or None."""
        async with self._session_factory() as session:
            result = await session.execute(
                select(UserORM).where(UserORM.login_id == login_id)
            )
            user = result.scalar_one_or_none()
            return user_to_dict(user, include_password=True) if user else None

    async def get_user_by_id(self, user_id):
        """Return the user (INCLUDING the password hash) matching user_id, or None."""
        async with self._session_factory() as session:
            user = await session.get(UserORM, user_id)
            return user_to_dict(user, include_password=True) if user else None

    async def update_user(self, user_id, username=None, password=None, role=None):
        """Update the provided fields (password re-hashed if given). Returns the
        updated user INCLUDING the password hash, or None if not found."""
        async with self._session_factory() as session:
            user = await session.get(UserORM, user_id)
            if not user:
                return None
            if username:
                user.username = username
            if password:
                user.password = _hash(password)
            if role:
                user.role = role
            await session.commit()
            await session.refresh(user)
            logger.info(f"✅ User updated: {user_id}")
            return user_to_dict(user, include_password=True)

    async def inactivate_user(self, user_id):
        """Set is_active=False. Returns the user WITHOUT the password field, or None."""
        async with self._session_factory() as session:
            user = await session.get(UserORM, user_id)
            if not user:
                return None
            user.is_active = False
            await session.commit()
            await session.refresh(user)
            logger.info(f"✅ User inactivated: {user_id}")
            return user_to_dict(user, include_password=False)

    async def activate_user(self, user_id):
        """Set is_active=True. Returns the user WITHOUT the password field, or None."""
        async with self._session_factory() as session:
            user = await session.get(UserORM, user_id)
            if not user:
                return None
            user.is_active = True
            await session.commit()
            await session.refresh(user)
            logger.info(f"✅ User activated: {user_id}")
            return user_to_dict(user, include_password=False)

    async def count_active_admins(self):
        """Return the number of currently active ADMIN users."""
        async with self._session_factory() as session:
            result = await session.execute(
                select(func.count()).select_from(UserORM).where(
                    UserORM.role == "ADMIN", UserORM.is_active.is_(True)
                )
            )
            return int(result.scalar_one() or 0)

    async def get_all_users(self):
        """Return all users (WITHOUT password), newest first."""
        async with self._session_factory() as session:
            result = await session.execute(
                select(UserORM).order_by(UserORM.created_at.desc())
            )
            return [user_to_dict(u, include_password=False) for u in result.scalars().all()]


class SqlAlchemyAuditRepository(AuditRepository):
    """AuditRepository implementation over a SQLAlchemy async session factory."""

    def __init__(self, session_factory):
        """Store the async session factory bound to the active engine."""
        self._session_factory = session_factory

    async def log_action(self, user_id, action, old_data=None, new_data=None, performed_by=None):
        """Persist an audit entry (old/new data serialized to JSON). Returns True on
        success, False on failure (best-effort; never raises)."""
        try:
            async with self._session_factory() as session:
                session.add(AuditLogORM(
                    user_id=user_id, action=action,
                    old_data=json.dumps(old_data) if old_data else None,
                    new_data=json.dumps(new_data) if new_data else None,
                    performed_by=performed_by,
                ))
                await session.commit()
            logger.info(f"✅ Audit logged: {action} for user_id {user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error logging audit action: {e}")
            return False
