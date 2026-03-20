"""
Application configuration using Pydantic Settings.

Environment variables are loaded from .env file or system environment.

SECURITY NOTE:
- Secrets (JWT key, database password, S3 keys) have NO defaults
- In development, you MUST provide secrets via .env file
- In production/staging, missing secrets will cause startup failure
"""

import secrets
import warnings
from functools import lru_cache
from typing import Optional, Union

from pydantic import Field, PostgresDsn, RedisDsn, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Known insecure default values that should never be used in production
INSECURE_SECRETS = {
    "your-super-secret-key-change-in-production",
    "dev-secret-key-for-local-development-32ch",
    "minioadmin",
    "changeme",
    "password",
    "secret",
}


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Campaign Operations OS"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = Field(default="development", pattern="^(development|staging|production)$")

    # API
    api_v1_prefix: str = "/api/v1"
    allowed_origins: Union[list[str], str] = ["http://localhost:3000"]

    # Database - NO DEFAULT for URL (contains credentials)
    database_url: Optional[PostgresDsn] = Field(
        default=None,
        description="PostgreSQL connection URL with credentials"
    )
    database_pool_size: int = 5
    database_max_overflow: int = 10
    database_echo: bool = False  # Log SQL queries

    # Redis - NO DEFAULT (may contain credentials in production)
    redis_url: Optional[RedisDsn] = Field(
        default=None,
        description="Redis connection URL"
    )

    # JWT Authentication - NO DEFAULT for secret key
    jwt_secret_key: Optional[str] = Field(
        default=None,
        description="Secret key for JWT signing (min 32 chars)"
    )
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # Password hashing
    password_hash_rounds: int = 12  # bcrypt rounds

    # S3/MinIO Storage - NO DEFAULTS for credentials
    s3_endpoint: Optional[str] = None
    s3_access_key: Optional[str] = Field(
        default=None,
        description="S3/MinIO access key"
    )
    s3_secret_key: Optional[str] = Field(
        default=None,
        description="S3/MinIO secret key"
    )
    s3_bucket_name: str = "campaign-os"
    s3_region: str = "us-east-1"
    s3_use_ssl: bool = False

    # File uploads
    max_upload_size_mb: int = 50
    allowed_file_types: list[str] = [
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "text/plain",
        "text/csv",
    ]

    # Email (for future use)
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: str = "noreply@campaign-os.local"
    smtp_from_name: str = "Campaign OS"

    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

    # Google OAuth (for Google Calendar integration)
    google_oauth_client_id: Optional[str] = None
    google_oauth_client_secret: Optional[str] = None

    # Token encryption (for OAuth tokens)
    # Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    token_encryption_key: Optional[str] = None

    # Base URLs for OAuth redirects
    api_base_url: str = "http://localhost:8000"
    frontend_base_url: str = "http://localhost:3000"

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        """Parse comma-separated origins string into list."""
        if isinstance(v, str):
            # Handle JSON-style list or comma-separated
            if v.startswith("["):
                import json
                return json.loads(v)
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v if v else ["http://localhost:3000"]

    @model_validator(mode="after")
    def validate_secrets_and_set_defaults(self) -> "Settings":
        """
        Validate that required secrets are provided and secure.

        In development: Generates temporary secrets with warnings
        In staging/production: Fails if secrets are missing or insecure
        """
        is_production = self.environment in ("staging", "production")
        missing_secrets = []
        insecure_secrets = []

        # Check JWT secret
        if not self.jwt_secret_key:
            if is_production:
                missing_secrets.append("JWT_SECRET_KEY")
            else:
                # Generate temporary secret for development
                self.jwt_secret_key = secrets.token_urlsafe(32)
                warnings.warn(
                    "JWT_SECRET_KEY not set. Using temporary random key. "
                    "Sessions will not persist across restarts. "
                    "Set JWT_SECRET_KEY in .env for persistent sessions.",
                    UserWarning,
                    stacklevel=2
                )
        elif len(self.jwt_secret_key) < 32:
            raise ValueError(
                f"JWT_SECRET_KEY must be at least 32 characters, got {len(self.jwt_secret_key)}"
            )
        elif self.jwt_secret_key.lower() in INSECURE_SECRETS:
            if is_production:
                insecure_secrets.append("JWT_SECRET_KEY")
            else:
                warnings.warn(
                    f"JWT_SECRET_KEY is using an insecure default value. "
                    "This is acceptable for development but MUST be changed for production.",
                    UserWarning,
                    stacklevel=2
                )

        # Check database URL
        if not self.database_url:
            if is_production:
                missing_secrets.append("DATABASE_URL")
            else:
                # Use default development database
                self.database_url = "postgresql://campaign_os:campaign_os@localhost:5432/campaign_os"
                warnings.warn(
                    "DATABASE_URL not set. Using default development database.",
                    UserWarning,
                    stacklevel=2
                )

        # Check Redis URL
        if not self.redis_url:
            if is_production:
                missing_secrets.append("REDIS_URL")
            else:
                # Use default development Redis
                self.redis_url = "redis://localhost:6379/0"

        # Check S3 credentials if endpoint is configured
        if self.s3_endpoint:
            if not self.s3_access_key:
                if is_production:
                    missing_secrets.append("S3_ACCESS_KEY")
                else:
                    self.s3_access_key = "minioadmin"
                    warnings.warn(
                        "S3_ACCESS_KEY not set. Using default MinIO credentials.",
                        UserWarning,
                        stacklevel=2
                    )
            elif self.s3_access_key.lower() in INSECURE_SECRETS and is_production:
                insecure_secrets.append("S3_ACCESS_KEY")

            if not self.s3_secret_key:
                if is_production:
                    missing_secrets.append("S3_SECRET_KEY")
                else:
                    self.s3_secret_key = "minioadmin"
            elif self.s3_secret_key.lower() in INSECURE_SECRETS and is_production:
                insecure_secrets.append("S3_SECRET_KEY")

        # Check Google OAuth secrets if client ID is configured
        if self.google_oauth_client_id and not self.google_oauth_client_secret:
            if is_production:
                missing_secrets.append("GOOGLE_OAUTH_CLIENT_SECRET")

        # Check token encryption key if Google OAuth is configured
        if self.google_oauth_client_id and not self.token_encryption_key:
            if is_production:
                missing_secrets.append("TOKEN_ENCRYPTION_KEY (required when Google OAuth is enabled)")
            else:
                warnings.warn(
                    "TOKEN_ENCRYPTION_KEY not set. Google OAuth tokens will not be encrypted. "
                    "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"",
                    UserWarning,
                    stacklevel=2
                )

        # Fail in production if secrets are missing or insecure
        if missing_secrets:
            raise ValueError(
                f"Missing required secrets for {self.environment} environment: "
                f"{', '.join(missing_secrets)}. "
                "Set these environment variables before starting the application."
            )

        if insecure_secrets:
            raise ValueError(
                f"Insecure secret values detected for {self.environment} environment: "
                f"{', '.join(insecure_secrets)}. "
                "These secrets are using known default values that are not safe for production."
            )

        return self

    @property
    def async_database_url(self) -> str:
        """Get async database URL for SQLAlchemy async engine."""
        return str(self.database_url).replace(
            "postgresql://", "postgresql+asyncpg://"
        )

    @property
    def sync_database_url(self) -> str:
        """Get sync database URL for Alembic migrations."""
        return str(self.database_url).replace(
            "postgresql+asyncpg://", "postgresql://"
        )

    @property
    def max_upload_size_bytes(self) -> int:
        """Get max upload size in bytes."""
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()


# Convenience instance
settings = get_settings()
