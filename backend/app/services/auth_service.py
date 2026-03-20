"""
Authentication Service

Handles all authentication-related business logic:
- User registration
- Login/logout
- Token management
- Password reset
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    hash_password,
    verify_password,
    create_token_pair,
    create_access_token,
    verify_refresh_token,
    create_password_reset_token,
    verify_password_reset_token,
    TokenPair,
)
from app.models import User
from app.schemas.auth import RegisterRequest, LoginRequest
from app.services.token_blacklist import (
    check_token_valid,
    blacklist_token,
    invalidate_all_user_tokens,
)


class AuthServiceError(Exception):
    """Base exception for auth service errors."""

    def __init__(self, message: str, code: str = "auth_error"):
        self.message = message
        self.code = code
        super().__init__(message)


class EmailAlreadyExistsError(AuthServiceError):
    """Raised when email is already registered."""

    def __init__(self):
        super().__init__("Email already registered", "email_exists")


class InvalidCredentialsError(AuthServiceError):
    """Raised when login credentials are invalid."""

    def __init__(self):
        super().__init__("Invalid email or password", "invalid_credentials")


class UserNotFoundError(AuthServiceError):
    """Raised when user is not found."""

    def __init__(self):
        super().__init__("User not found", "user_not_found")


class UserInactiveError(AuthServiceError):
    """Raised when user account is inactive."""

    def __init__(self):
        super().__init__("User account is inactive", "user_inactive")


class InvalidTokenError(AuthServiceError):
    """Raised when token is invalid or expired."""

    def __init__(self):
        super().__init__("Invalid or expired token", "invalid_token")


class InvalidPasswordError(AuthServiceError):
    """Raised when current password is incorrect."""

    def __init__(self):
        super().__init__("Current password is incorrect", "invalid_password")


class AuthService:
    """Service for handling authentication operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email address."""
        result = await self.db.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get a user by ID."""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def register(self, data: RegisterRequest) -> tuple[User, TokenPair]:
        """
        Register a new user.

        Args:
            data: Registration data

        Returns:
            Tuple of (user, token_pair)

        Raises:
            EmailAlreadyExistsError: If email is already registered
        """
        # Check if email already exists
        existing_user = await self.get_user_by_email(data.email)
        if existing_user:
            raise EmailAlreadyExistsError()

        # Create new user
        user = User(
            email=data.email.lower(),
            password_hash=hash_password(data.password),
            full_name=data.full_name,
            phone=data.phone,
            is_active=True,
            is_superadmin=False,
        )

        self.db.add(user)
        await self.db.flush()  # Get the user ID
        await self.db.refresh(user)

        # Generate tokens
        tokens = create_token_pair(user.id)

        return user, tokens

    async def login(self, data: LoginRequest) -> tuple[User, TokenPair]:
        """
        Authenticate a user and return tokens.

        Args:
            data: Login credentials

        Returns:
            Tuple of (user, token_pair)

        Raises:
            InvalidCredentialsError: If credentials are invalid
            UserInactiveError: If user account is inactive
        """
        # Find user by email
        user = await self.get_user_by_email(data.email)
        if not user:
            raise InvalidCredentialsError()

        # Verify password
        if not verify_password(data.password, user.password_hash):
            raise InvalidCredentialsError()

        # Check if user is active
        if not user.is_active:
            raise UserInactiveError()

        # Update last login time
        user.last_login_at = datetime.now(timezone.utc)
        await self.db.flush()

        # Generate tokens
        tokens = create_token_pair(user.id)

        return user, tokens

    async def refresh_tokens(self, refresh_token: str) -> tuple[User, TokenPair]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            Tuple of (user, new_token_pair)

        Raises:
            InvalidTokenError: If refresh token is invalid or blacklisted
            UserNotFoundError: If user no longer exists
            UserInactiveError: If user is inactive
        """
        # Verify refresh token signature
        user_id = verify_refresh_token(refresh_token)
        if not user_id:
            raise InvalidTokenError()

        # Check if token is blacklisted or user tokens invalidated
        is_valid, _ = await check_token_valid(refresh_token)
        if not is_valid:
            raise InvalidTokenError()

        # Get user
        user = await self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError()

        if not user.is_active:
            raise UserInactiveError()

        # Blacklist the old refresh token (token rotation)
        await blacklist_token(refresh_token)

        # Generate new token pair
        tokens = create_token_pair(user.id)

        return user, tokens

    async def request_password_reset(self, email: str) -> Optional[str]:
        """
        Generate password reset token.

        Args:
            email: User's email address

        Returns:
            Reset token if user exists, None otherwise
            (We return None instead of raising an error to prevent
            email enumeration attacks)
        """
        user = await self.get_user_by_email(email)
        if not user or not user.is_active:
            return None

        # Generate reset token
        token = create_password_reset_token(user.id, user.email)
        return token

    async def reset_password(self, token: str, new_password: str) -> User:
        """
        Reset password using reset token.

        Args:
            token: Password reset token
            new_password: New password

        Returns:
            Updated user

        Raises:
            InvalidTokenError: If token is invalid or expired
            UserNotFoundError: If user no longer exists
        """
        # Verify token
        payload = verify_password_reset_token(token)
        if not payload:
            raise InvalidTokenError()

        # Get user
        user = await self.get_user_by_id(payload["user_id"])
        if not user:
            raise UserNotFoundError()

        # Verify email matches (extra security)
        if user.email.lower() != payload["email"].lower():
            raise InvalidTokenError()

        # Update password
        user.password_hash = hash_password(new_password)
        await self.db.flush()

        # Invalidate all existing tokens for security
        await invalidate_all_user_tokens(user.id)

        return user

    async def change_password(
        self,
        user: User,
        current_password: str,
        new_password: str,
    ) -> User:
        """
        Change password for authenticated user.

        Args:
            user: Current user
            current_password: Current password for verification
            new_password: New password

        Returns:
            Updated user

        Raises:
            InvalidPasswordError: If current password is incorrect
        """
        # Verify current password
        if not verify_password(current_password, user.password_hash):
            raise InvalidPasswordError()

        # Update password
        user.password_hash = hash_password(new_password)
        await self.db.flush()

        return user

    async def update_profile(
        self,
        user: User,
        full_name: Optional[str] = None,
        phone: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> User:
        """
        Update user profile.

        Args:
            user: User to update
            full_name: New full name (optional)
            phone: New phone number (optional)
            avatar_url: New avatar URL (optional)

        Returns:
            Updated user
        """
        if full_name is not None:
            user.full_name = full_name
        if phone is not None:
            user.phone = phone
        if avatar_url is not None:
            user.avatar_url = avatar_url

        await self.db.flush()
        await self.db.refresh(user)

        return user

    async def verify_email(self, user: User) -> User:
        """
        Mark user's email as verified.

        Args:
            user: User to verify

        Returns:
            Updated user
        """
        user.email_verified_at = datetime.now(timezone.utc)
        await self.db.flush()
        return user

    async def deactivate_user(self, user: User) -> User:
        """
        Deactivate a user account.

        Args:
            user: User to deactivate

        Returns:
            Updated user
        """
        user.is_active = False
        await self.db.flush()
        return user
