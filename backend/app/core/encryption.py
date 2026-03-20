"""
Token encryption utilities.

Provides pluggable encryption for sensitive data like OAuth tokens.
If no encryption key is configured, data is stored in plaintext (for development).
"""

import base64
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Optional import - only needed if encryption is enabled
try:
    from cryptography.fernet import Fernet, InvalidToken
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    Fernet = None
    InvalidToken = Exception


class TokenEncryption:
    """
    Pluggable encryption for OAuth tokens and other sensitive data.

    Usage:
        # Initialize at app startup
        TokenEncryption.initialize(settings.token_encryption_key)

        # Encrypt/decrypt
        encrypted = TokenEncryption.encrypt("my-secret-token")
        decrypted = TokenEncryption.decrypt(encrypted)

    If no key is provided, encryption is disabled and values pass through unchanged.
    This allows for easy development without encryption overhead.
    """

    _cipher: Optional["Fernet"] = None
    _initialized: bool = False

    @classmethod
    def initialize(cls, key: Optional[str] = None) -> None:
        """
        Initialize encryption with a Fernet key.

        Args:
            key: Base64-encoded 32-byte Fernet key, or None to disable encryption.

        To generate a key:
            python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
        """
        cls._initialized = True

        if key is None:
            cls._cipher = None
            logger.warning(
                "Token encryption is DISABLED. "
                "Set TOKEN_ENCRYPTION_KEY in production."
            )
            return

        if not CRYPTOGRAPHY_AVAILABLE:
            raise RuntimeError(
                "cryptography package is required for token encryption. "
                "Install with: pip install cryptography"
            )

        try:
            # Validate key format
            cls._cipher = Fernet(key.encode() if isinstance(key, str) else key)
            logger.info("Token encryption initialized successfully.")
        except Exception as e:
            raise ValueError(
                f"Invalid encryption key format: {e}. "
                "Key must be a valid Fernet key (base64-encoded 32-byte key)."
            )

    @classmethod
    def encrypt(cls, value: str) -> str:
        """
        Encrypt a string value.

        Args:
            value: Plaintext string to encrypt.

        Returns:
            Encrypted string (base64-encoded) or original value if encryption disabled.
        """
        if not cls._initialized:
            # Auto-initialize without encryption for convenience in development
            cls.initialize(None)

        if cls._cipher is None:
            return value

        encrypted = cls._cipher.encrypt(value.encode())
        return encrypted.decode()

    @classmethod
    def decrypt(cls, value: str) -> str:
        """
        Decrypt an encrypted string value.

        Args:
            value: Encrypted string (base64-encoded) or plaintext if encryption disabled.

        Returns:
            Decrypted plaintext string.

        Raises:
            ValueError: If decryption fails (invalid token or wrong key).
        """
        if not cls._initialized:
            cls.initialize(None)

        if cls._cipher is None:
            return value

        try:
            decrypted = cls._cipher.decrypt(value.encode())
            return decrypted.decode()
        except InvalidToken as e:
            raise ValueError(
                "Failed to decrypt token. "
                "This may indicate the encryption key has changed or data is corrupted."
            ) from e

    @classmethod
    def is_enabled(cls) -> bool:
        """Check if encryption is enabled."""
        return cls._cipher is not None

    @classmethod
    def generate_key(cls) -> str:
        """
        Generate a new Fernet encryption key.

        Returns:
            Base64-encoded 32-byte key suitable for TOKEN_ENCRYPTION_KEY.
        """
        if not CRYPTOGRAPHY_AVAILABLE:
            raise RuntimeError(
                "cryptography package is required. Install with: pip install cryptography"
            )
        return Fernet.generate_key().decode()
