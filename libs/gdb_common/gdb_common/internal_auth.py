"""Shared inter-service authentication (Enterprise remediation Phase 3.1 / M-3).

Replaces the ~6 copy-pasted `verify_internal_api_key` dependencies. The shared
secret lives in each service's own settings, so the verifier is built per service
by injecting a key-provider callable — the shared package never imports any
service's settings. Comparison is constant-time (C-2).
"""

import hmac
from typing import Callable

from fastapi import Header, HTTPException, status


def make_internal_api_key_verifier(get_api_key: Callable[[], str]):
    """Return a FastAPI dependency that rejects internal calls lacking the key.

    get_api_key is called per request, so it always reads the current config.
    """

    async def verify_internal_api_key(
        x_internal_api_key: str = Header(None, alias="X-Internal-API-Key"),
    ):
        """Validate the X-Internal-API-Key header via constant-time comparison.

        Args:
            x_internal_api_key: Value of the inbound X-Internal-API-Key header.

        Returns:
            True when the key matches the configured internal secret.

        Raises:
            HTTPException(401): If the header is missing or does not match.
        """
        expected = get_api_key() or ""
        if not x_internal_api_key or not hmac.compare_digest(x_internal_api_key, expected):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error_code": "UNAUTHORIZED",
                    "message": "Missing or invalid internal API key",
                },
            )
        return True

    return verify_internal_api_key
