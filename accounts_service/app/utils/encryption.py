"""
Accounts Service - Encryption Utilities

Encryption/decryption for sensitive data (PIN, passwords).

Author: GDB Architecture Team
"""

import bcrypt
import hmac
import logging
import base64
import hashlib
from cryptography.fernet import Fernet

from app.config.settings import settings

logger = logging.getLogger(__name__)


class EncryptionManager:
    """
    Handles encryption and hashing of sensitive data.

    Uses bcrypt for password/PIN hashing with salt rounds.
    """

    # Bcrypt salt rounds (higher = more secure but slower)
    SALT_ROUNDS = 12

    # Symmetric encryption key for reversible Fernet data.
    # Derive a STABLE 32-byte Fernet key deterministically from the configured
    # PIN_ENCRYPTION_KEY so the key survives process restarts (a random
    # Fernet.generate_key() per boot would make previously-encrypted data
    # undecryptable). The configured secret should be set via env in production.
    _SECRET_KEY = base64.urlsafe_b64encode(
        hashlib.sha256(settings.PIN_ENCRYPTION_KEY.encode()).digest()
    )
    _fernet = Fernet(_SECRET_KEY)
    
    @staticmethod
    def hash_pin(pin: str) -> str:
        """
        Hash a PIN using bcrypt.
        
        Args:
            pin: Plain text PIN
            
        Returns:
            Bcrypt hash
        """
        salt = bcrypt.gensalt(rounds=EncryptionManager.SALT_ROUNDS)
        hash_value = bcrypt.hashpw(pin.encode('utf-8'), salt)
        return hash_value.decode('utf-8')
    
    @staticmethod
    def verify_pin(pin: str, pin_hash: str) -> bool:
        """
        Verify PIN against hash.
        
        Args:
            pin: Plain text PIN
            pin_hash: Stored hash
            
        Returns:
            True if PIN matches, False otherwise
        """
        try:
            return bcrypt.checkpw(pin.encode('utf-8'), pin_hash.encode('utf-8'))
        except Exception as e:
            logger.error(f"❌ PIN verification error: {e}")
            return False
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Bcrypt hash
        """
        salt = bcrypt.gensalt(rounds=EncryptionManager.SALT_ROUNDS)
        hash_value = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hash_value.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        Verify password against hash.
        
        Args:
            password: Plain text password
            password_hash: Stored hash
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception as e:
            logger.error(f"❌ Password verification error: {e}")
            return False

    @staticmethod
    def encrypt_data(data: str) -> str:
        """Encrypt string data using Fernet."""
        if not data:
            return ""
        return EncryptionManager._fernet.encrypt(data.encode()).decode()

    @staticmethod
    def decrypt_data(token: str) -> str:
        """Decrypt string data using Fernet."""
        if not token:
            return ""
        return EncryptionManager._fernet.decrypt(token.encode()).decode()

    @staticmethod
    def blind_index(value: str) -> str:
        """Deterministic keyed hash (HMAC-SHA256) for equality lookups on
        encrypted PII (e.g. Aadhaar). Fernet ciphertext is non-deterministic, so
        uniqueness/lookup is enforced on this stable index instead of the
        ciphertext. Enterprise remediation H-4."""
        if not value:
            return ""
        key = hashlib.sha256((settings.PIN_ENCRYPTION_KEY + "|blind-index").encode()).digest()
        return hmac.new(key, value.encode(), hashlib.sha256).hexdigest()
