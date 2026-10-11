"""
RS256 dual-mode JWT tests (Enterprise remediation C-1).

Proves the signing/verification layer:
- defaults to HS256 (backward compatible) when no keys are configured,
- signs + verifies with RS256 when an asymmetric key pair is configured,
- during migration, still accepts legacy HS256 tokens when a public key is set.
"""

from datetime import datetime, timedelta, UTC

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException

from app.config.settings import settings
from app.security.jwt_utils import JWTUtil
from app.security.jwt_validation import JWTValidator


def _rsa_pem_pair():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    public_pem = key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return private_pem, public_pem


def test_hs256_default_roundtrip():
    """No RS keys configured → HS256, unchanged behaviour."""
    token = JWTUtil.generate_token("1", "admin", "ADMIN")
    assert jwt.get_unverified_header(token)["alg"] == "HS256"
    claims = JWTUtil.verify_token(token)
    assert claims["login_id"] == "admin"
    assert claims["role"] == "ADMIN"


def test_rs256_roundtrip(monkeypatch):
    """Private+public key configured → RS256 sign & verify; tampering rejected."""
    private_pem, public_pem = _rsa_pem_pair()
    monkeypatch.setattr(settings, "JWT_PRIVATE_KEY", private_pem, raising=False)
    monkeypatch.setattr(settings, "JWT_PUBLIC_KEY", public_pem, raising=False)

    token = JWTUtil.generate_token("2", "teller", "TELLER")
    assert jwt.get_unverified_header(token)["alg"] == "RS256"
    claims = JWTUtil.verify_token(token)
    assert claims["role"] == "TELLER"

    with pytest.raises(jwt.InvalidTokenError):
        JWTUtil.verify_token(token + "tampered")


def test_migration_accepts_legacy_hs256(monkeypatch):
    """With only a public key set, a legacy HS256 token must still verify."""
    _private_pem, public_pem = _rsa_pem_pair()
    legacy_hs_token = JWTUtil.generate_token("3", "mgr", "MANAGER")  # signed HS256
    monkeypatch.setattr(settings, "JWT_PUBLIC_KEY", public_pem, raising=False)

    claims = JWTUtil.verify_token(legacy_hs_token)
    assert claims["login_id"] == "mgr"


# ---- Cross-service verifier (JWTValidator.validate_token) dual-mode ----
def _rs256_token(private_pem, role="TELLER"):
    exp = int((datetime.now(UTC) + timedelta(hours=1)).timestamp())
    claims = {"sub": "9", "login_id": "svc", "role": role, "exp": exp}
    return jwt.encode(claims, private_pem, algorithm="RS256")


def test_validator_hs256_default():
    token = JWTUtil.generate_token("1", "admin", "ADMIN")
    claims = JWTValidator.validate_token(token, settings.JWT_SECRET_KEY, "HS256")
    assert claims["role"] == "ADMIN"


def test_validator_accepts_rs256_when_public_key_set():
    private_pem, public_pem = _rsa_pem_pair()
    rs_token = _rs256_token(private_pem, role="TELLER")
    claims = JWTValidator.validate_token(
        rs_token, settings.JWT_SECRET_KEY, "HS256", public_key=public_pem
    )
    assert claims["role"] == "TELLER"


def test_validator_still_accepts_legacy_hs256_during_migration():
    _private_pem, public_pem = _rsa_pem_pair()
    hs_token = JWTUtil.generate_token("2", "mgr", "MANAGER")  # HS256
    claims = JWTValidator.validate_token(
        hs_token, settings.JWT_SECRET_KEY, "HS256", public_key=public_pem
    )
    assert claims["login_id"] == "mgr"


def test_validator_rejects_garbage():
    with pytest.raises(HTTPException) as exc:
        JWTValidator.validate_token("not.a.valid.token", settings.JWT_SECRET_KEY, "HS256")
    assert exc.value.status_code == 401
