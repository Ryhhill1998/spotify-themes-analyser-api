from unittest.mock import Mock, MagicMock

from fastapi.testclient import TestClient

from api.dependencies import get_spotify_auth_service
from api.main import app
from api.services.music.spotify_auth_service import SpotifyAuthService

print(app.routes)

client = TestClient(app)


def override_dep():
    mock = MagicMock(spec=SpotifyAuthService)
    mock.generate_auth_url.return_value = "hello"
    return mock


def test_login():
    app.dependency_overrides[get_spotify_auth_service] = override_dep
    res = client.get("/auth/spotify/login", follow_redirects=False)
    assert res.status_code == 307
    assert res.headers.get("location") == "hello"
