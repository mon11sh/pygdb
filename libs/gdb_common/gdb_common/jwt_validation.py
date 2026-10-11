"""
JWT Validation and Authorization Module

Shared utilities for JWT validation and role-based access control.
Used by all microservices to validate tokens issued by Auth Service.

This module provides:
- JWT validation (signature, expiry)
- Role extraction from JWT
- Role-based access control helpers
- FastAPI dependency for authorization

Author: GDB Architecture Team
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, UTC
from functools import lru_cache

from jose import jwt, JWTError, ExpiredSignatureError
from fastapi import HTTPException, status, Header

logger = logging.getLogger(__name__)


class JWTValidationConfig:
    """Configuration for JWT validation."""
    
    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
    ):
        """
        Initialize JWT validation configuration.
        
        Args:
            secret_key: Secret key used to sign JWT tokens
            algorithm: JWT algorithm (default: HS256)
        """
        self.secret_key = secret_key
        self.algorithm = algorithm


class JWTValidator:
    """JWT validation and role extraction utilities."""
    
    @staticmethod
    def validate_token(
        token: str,
        secret_key: str,
        algorithm: str = "HS256",
        public_key: str = "",
    ) -> Dict[str, Any]:
        """
        Validate JWT token and return claims.

        Args:
            token: JWT token string
            secret_key: Secret key used to sign HS256 tokens
            algorithm: HS256 algorithm name
            public_key: RS256 public key (PEM). When set, RS256 tokens are
                accepted using this key AND legacy HS256 tokens still verify,
                so a fleet can migrate one service at a time (remediation C-1).

        Returns:
            Dictionary of JWT claims

        Raises:
            HTTPException(401): If token is invalid or expired
        """
        # Build the ordered list of (key, algorithm) pairs to try. RS256 first
        # when a public key is configured, then legacy HS256.
        candidates = []
        if public_key and public_key.strip():
            candidates.append((public_key, "RS256"))
        candidates.append((secret_key, algorithm))

        last_error: Optional[Exception] = None
        for key, alg in candidates:
            try:
                return jwt.decode(token, key, algorithms=[alg])
            except ExpiredSignatureError:
                # Expiry is definitive regardless of key — stop immediately.
                logger.warning("Token has expired")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            except JWTError as e:
                last_error = e
                continue
            except Exception as e:  # pragma: no cover - defensive
                last_error = e
                continue

        logger.warning(f"Invalid token: {str(last_error)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    @staticmethod
    def extract_token_from_header(
        authorization: Optional[str],
    ) -> str:
        """
        Extract JWT token from Authorization header.
        
        Expected format: "Bearer <token>"
        
        Args:
            authorization: Authorization header value
        
        Returns:
            Token string
        
        Raises:
            HTTPException(401): If header is missing or malformed
        """
        if not authorization:
            logger.warning("Missing Authorization header")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing Authorization header",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Do NOT log token material (header prefix, parts, or bytes). Log only
        # presence so credentials never end up in logs.
        logger.debug("Authorization header present: true")

        parts = authorization.split()

        if len(parts) != 2 or parts[0].lower() != "bearer":
            logger.warning(f"Invalid Authorization header format")
            logger.warning(f"Expected exactly 2 parts with first being 'Bearer', got {len(parts)} parts")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Authorization header format. Expected: Bearer <token>",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return parts[1]
    
    @staticmethod
    def get_role(claims: Dict[str, Any]) -> str:
        """
        Extract user role from JWT claims.
        
        Args:
            claims: JWT claims dictionary
        
        Returns:
            User role (ADMIN, TELLER, or MANAGER)
        
        Raises:
            HTTPException(401): If role is missing or invalid
        """
        role = claims.get("role")
        if not role:
            logger.warning("Role missing from JWT claims")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Role missing from token",
            )
        
        valid_roles = ["ADMIN", "TELLER", "MANAGER"]
        if role not in valid_roles:
            logger.warning(f"Invalid role in JWT: {role}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid role: {role}",
            )
        
        return role
    
    @staticmethod
    def get_user_id(claims: Dict[str, Any]) -> int:
        """
        Extract user_id from JWT claims.
        
        Args:
            claims: JWT claims dictionary
        
        Returns:
            User ID (integer)
        
        Raises:
            HTTPException(401): If user_id is missing or invalid
        """
        # Try to get user_id, fall back to "sub" claim (subject)
        user_id = claims.get("user_id") or claims.get("sub")
        if user_id is None:
            logger.warning("user_id missing from JWT claims")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="user_id missing from token",
            )
        
        try:
            return int(user_id)
        except (ValueError, TypeError):
            logger.warning(f"Invalid user_id in JWT: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user_id format",
            )
    
    @staticmethod
    def get_login_id(claims: Dict[str, Any]) -> str:
        """
        Extract login_id from JWT claims.
        
        Args:
            claims: JWT claims dictionary
        
        Returns:
            Login ID (string)
        
        Raises:
            HTTPException(401): If login_id is missing
        """
        login_id = claims.get("login_id")
        if not login_id:
            logger.warning("login_id missing from JWT claims")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="login_id missing from token",
            )
        
        return login_id


class RoleChecker:
    """Role-based access control helpers."""
    
    @staticmethod
    def check_role(
        user_role: str,
        allowed_roles: List[str],
    ) -> bool:
        """
        Check if user role is in allowed roles.
        
        Args:
            user_role: User role from JWT
            allowed_roles: List of allowed roles
        
        Returns:
            True if user role is allowed, False otherwise
        """
        return user_role in allowed_roles
    
    @staticmethod
    def require_role(
        user_role: str,
        allowed_roles: List[str],
    ) -> None:
        """
        Require user to have one of the allowed roles.
        Raises HTTPException(403) if role not allowed.
        
        Args:
            user_role: User role from JWT
            allowed_roles: List of allowed roles
        
        Raises:
            HTTPException(403): If user role not in allowed roles
        """
        if not RoleChecker.check_role(user_role, allowed_roles):
            logger.warning(
                f"Access denied: role '{user_role}' not in {allowed_roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {', '.join(allowed_roles)}",
            )
    
    @staticmethod
    def require_same_user_or_admin(
        user_id: int,
        requested_user_id: int,
        user_role: str,
    ) -> None:
        """
        Require user to be either ADMIN or the requested user.
        Used for endpoints where users can view/edit their own profile.
        
        Args:
            user_id: User ID from JWT
            requested_user_id: User ID being requested
            user_role: User role from JWT
        
        Raises:
            HTTPException(403): If user is not ADMIN and user_id doesn't match
        """
        if user_role != "ADMIN" and user_id != requested_user_id:
            logger.warning(
                f"Access denied: user {user_id} tried to access user {requested_user_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own profile",
            )
    
    @staticmethod
    def require_role_for_admin_action(
        user_role: str,
        admin_only: bool = False,
    ) -> None:
        """
        Require user to be ADMIN for admin-only actions.
        
        Args:
            user_role: User role from JWT
            admin_only: If True, only ADMIN allowed. If False, ADMIN or TELLER allowed.
        
        Raises:
            HTTPException(403): If role requirements not met
        """
        allowed = ["ADMIN"] if admin_only else ["ADMIN", "TELLER"]
        RoleChecker.require_role(user_role, allowed)
