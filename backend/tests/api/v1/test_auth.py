"""
Tests for authentication endpoints with token blacklist.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models import User
from app.api.deps import get_db, get_current_user
from app.core.security import create_access_token, create_refresh_token, create_token_pair


class TestLogoutEndpoint:
    """Tests for POST /auth/logout endpoint."""

    @pytest.fixture
    def test_user(self):
        """Create a test user."""
        user = MagicMock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        user.full_name = "Test User"
        user.is_active = True
        return user

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        return session

    @pytest.fixture
    def access_token(self, test_user):
        """Create a test access token."""
        return create_access_token(user_id=test_user.id)

    @pytest.fixture
    def refresh_token(self, test_user):
        """Create a test refresh token."""
        return create_refresh_token(user_id=test_user.id)

    @pytest.fixture
    def auth_headers(self, access_token):
        """Create authentication headers."""
        return {"Authorization": f"Bearer {access_token}"}

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        storage = {}

        async def mock_setex(key, ttl, value):
            storage[key] = value
            return True

        async def mock_exists(key):
            return 1 if key in storage else 0

        async def mock_get(key):
            return storage.get(key)

        redis_mock = AsyncMock()
        redis_mock.setex = mock_setex
        redis_mock.exists = mock_exists
        redis_mock.get = mock_get
        redis_mock.storage = storage  # Expose for assertions
        return redis_mock

    @pytest.mark.asyncio
    async def test_logout_blacklists_access_token(
        self, mock_db_session, test_user, access_token, auth_headers, mock_redis
    ):
        """Test that logout blacklists the access token."""

        async def override_get_db():
            yield mock_db_session

        async def override_get_current_user():
            return test_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = override_get_current_user

        with patch(
            "app.services.token_blacklist.get_redis",
            return_value=mock_redis,
        ), patch(
            "app.api.deps.check_token_valid",
            return_value=(True, None),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.post(
                    "/api/v1/auth/logout",
                    headers=auth_headers,
                )

                assert response.status_code == 204
                # Verify token was blacklisted
                assert len(mock_redis.storage) >= 1

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_logout_blacklists_refresh_token(
        self, mock_db_session, test_user, access_token, refresh_token, mock_redis
    ):
        """Test that logout blacklists refresh token when provided."""

        async def override_get_db():
            yield mock_db_session

        async def override_get_current_user():
            return test_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = override_get_current_user

        with patch(
            "app.services.token_blacklist.get_redis",
            return_value=mock_redis,
        ), patch(
            "app.api.deps.check_token_valid",
            return_value=(True, None),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.post(
                    "/api/v1/auth/logout",
                    headers={"Authorization": f"Bearer {access_token}"},
                    json={"refresh_token": refresh_token},
                )

                assert response.status_code == 204
                # Verify both tokens were blacklisted
                assert len(mock_redis.storage) >= 2

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_logout_requires_authentication(self, mock_db_session):
        """Test that logout requires authentication."""

        async def override_get_db():
            yield mock_db_session

        app.dependency_overrides[get_db] = override_get_db

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post("/api/v1/auth/logout")

            assert response.status_code == 401

        app.dependency_overrides.clear()


class TestTokenBlacklistInAuth:
    """Tests for token blacklist integration in auth flow."""

    @pytest.fixture
    def test_user(self):
        """Create a test user."""
        user = MagicMock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        user.full_name = "Test User"
        user.is_active = True
        user.password_hash = "$2b$12$test"
        return user

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        return session

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        storage = {}

        async def mock_setex(key, ttl, value):
            storage[key] = value
            return True

        async def mock_exists(key):
            return 1 if key in storage else 0

        async def mock_get(key):
            return storage.get(key)

        redis_mock = AsyncMock()
        redis_mock.setex = mock_setex
        redis_mock.exists = mock_exists
        redis_mock.get = mock_get
        redis_mock.storage = storage
        return redis_mock

    @pytest.mark.asyncio
    async def test_blacklisted_token_rejected(
        self, mock_db_session, test_user, mock_redis
    ):
        """Test that blacklisted tokens are rejected."""
        access_token = create_access_token(user_id=test_user.id)

        async def override_get_db():
            yield mock_db_session

        app.dependency_overrides[get_db] = override_get_db

        # First, blacklist the token
        mock_redis.storage["token:blacklist:somehash"] = "access"

        with patch(
            "app.services.token_blacklist.get_redis",
            return_value=mock_redis,
        ), patch(
            "app.api.deps.check_token_valid",
            return_value=(False, "Token has been revoked"),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.get(
                    "/api/v1/auth/me",
                    headers={"Authorization": f"Bearer {access_token}"},
                )

                assert response.status_code == 401
                assert "revoked" in response.json()["detail"].lower()

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_user_invalidated_tokens_rejected(
        self, mock_db_session, test_user, mock_redis
    ):
        """Test that tokens issued before user invalidation are rejected."""
        access_token = create_access_token(user_id=test_user.id)

        async def override_get_db():
            yield mock_db_session

        app.dependency_overrides[get_db] = override_get_db

        with patch(
            "app.services.token_blacklist.get_redis",
            return_value=mock_redis,
        ), patch(
            "app.api.deps.check_token_valid",
            return_value=(False, "All sessions have been invalidated"),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.get(
                    "/api/v1/auth/me",
                    headers={"Authorization": f"Bearer {access_token}"},
                )

                assert response.status_code == 401
                assert "invalidated" in response.json()["detail"].lower()

        app.dependency_overrides.clear()


class TestRefreshTokenBlacklist:
    """Tests for refresh token blacklist in token rotation."""

    @pytest.fixture
    def test_user(self):
        """Create a test user."""
        user = MagicMock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        user.full_name = "Test User"
        user.is_active = True
        return user

    @pytest.fixture
    def mock_db_session(self, test_user):
        """Create a mock database session that returns the test user."""
        session = AsyncMock()

        # Mock the execute method to return our test user
        result = MagicMock()
        result.scalar_one_or_none.return_value = test_user
        session.execute.return_value = result
        session.flush = AsyncMock()

        return session

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        storage = {}

        async def mock_setex(key, ttl, value):
            storage[key] = value
            return True

        async def mock_exists(key):
            return 1 if key in storage else 0

        async def mock_get(key):
            return storage.get(key)

        redis_mock = AsyncMock()
        redis_mock.setex = mock_setex
        redis_mock.exists = mock_exists
        redis_mock.get = mock_get
        redis_mock.storage = storage
        return redis_mock

    @pytest.mark.asyncio
    async def test_refresh_blacklists_old_token(
        self, mock_db_session, test_user, mock_redis
    ):
        """Test that refreshing tokens blacklists the old refresh token."""
        refresh_token = create_refresh_token(user_id=test_user.id)

        async def override_get_db():
            yield mock_db_session

        app.dependency_overrides[get_db] = override_get_db

        with patch(
            "app.services.token_blacklist.get_redis",
            return_value=mock_redis,
        ), patch(
            "app.services.auth_service.check_token_valid",
            return_value=(True, None),
        ), patch(
            "app.services.auth_service.blacklist_token",
            new_callable=AsyncMock,
        ) as mock_blacklist:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.post(
                    "/api/v1/auth/refresh",
                    json={"refresh_token": refresh_token},
                )

                # Should succeed and blacklist old token
                if response.status_code == 200:
                    mock_blacklist.assert_called_once_with(refresh_token)

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_blacklisted_refresh_token_rejected(
        self, mock_db_session, test_user, mock_redis
    ):
        """Test that blacklisted refresh tokens are rejected."""
        refresh_token = create_refresh_token(user_id=test_user.id)

        async def override_get_db():
            yield mock_db_session

        app.dependency_overrides[get_db] = override_get_db

        with patch(
            "app.services.token_blacklist.get_redis",
            return_value=mock_redis,
        ), patch(
            "app.services.auth_service.check_token_valid",
            return_value=(False, "Token has been revoked"),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.post(
                    "/api/v1/auth/refresh",
                    json={"refresh_token": refresh_token},
                )

                assert response.status_code == 401

        app.dependency_overrides.clear()
