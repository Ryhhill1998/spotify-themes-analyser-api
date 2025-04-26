from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from api.dependencies import get_spotify_auth_service, get_settings
from api.main import app
from api.data_structures.models import TokenData
from api.services.music.spotify_auth_service import SpotifyAuthService, SpotifyAuthServiceException
from api.settings import Settings

# 1. Test that /auth/spotify/login returns expected redirect response.
# 2. Test that /auth/spotify/callback returns error response if request cannot be authenticated.
# 3. Test that /auth/spotify/callback returns error response if the spotify auth service fails to create tokens.
# 4. Test that /auth/spotify/callback returns expected redirected response.

TEST_FRONTEND_URL = "http://test-frontend-url.com"
MOCK_OAUTH_STATE = "12345"


@pytest.fixture
def mock_spotify_auth_service() -> MagicMock:
    return MagicMock(spec=SpotifyAuthService)


@pytest.fixture
def mock_settings() -> MagicMock:
    mock = MagicMock(spec=Settings)
    mock.frontend_url = TEST_FRONTEND_URL
    return mock


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, follow_redirects=False)


def test_login_success(client, mock_spotify_auth_service):
    location = "test"
    app.dependency_overrides[get_spotify_auth_service] = lambda: mock_spotify_auth_service
    mock_spotify_auth_service.generate_auth_url.return_value = location

    res = client.get("/auth/spotify/login")

    headers = res.headers
    assert (
            res.status_code == 307 and
            headers["location"] == location and
            "oauth_state" in headers["set-cookie"]
    )


def test_callback_state_authentication_failure(client, mock_settings):
    app.dependency_overrides[get_settings] = lambda: mock_settings

    # state request param mismatch with cookie oauth_state
    client.cookies.set("oauth_state", MOCK_OAUTH_STATE)
    res = client.get(f"/auth/spotify/callback?code=code&state=state")

    assert (
            res.status_code == 307 and
            res.headers["location"] == f"{TEST_FRONTEND_URL}/#error=authentication-failure"
    )


def test_callback_auth_service_failure(client, mock_spotify_auth_service, mock_settings):
    app.dependency_overrides[get_spotify_auth_service] = lambda: mock_spotify_auth_service
    app.dependency_overrides[get_settings] = lambda: mock_settings
    mock_spotify_auth_service.create_tokens.side_effect = SpotifyAuthServiceException("Test")

    # state request param matches cookie oauth_state
    client.cookies.set("oauth_state", MOCK_OAUTH_STATE)
    res = client.get(f"/auth/spotify/callback?code=code&state={MOCK_OAUTH_STATE}")

    assert (
            res.status_code == 307 and
            res.headers["location"] == f"{TEST_FRONTEND_URL}/#error=authentication-failure"
    )


def test_callback_success(client, mock_spotify_auth_service, mock_settings):
    app.dependency_overrides[get_spotify_auth_service] = lambda: mock_spotify_auth_service
    app.dependency_overrides[get_settings] = lambda: mock_settings
    mock_spotify_auth_service.create_tokens.return_value = TokenData(access_token="access", refresh_token="refresh")

    # state request param matches cookie oauth_state
    client.cookies.set("oauth_state", MOCK_OAUTH_STATE)
    res = client.get(f"/auth/spotify/callback?code=code&state={MOCK_OAUTH_STATE}")

    headers = res.headers
    assert (
            res.status_code == 307 and
            headers["location"] == TEST_FRONTEND_URL and
            "access" in headers["set-cookie"] and
            "refresh" in headers["set-cookie"]
    )
