from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from api.dependencies import get_spotify_data_service, get_insights_service, get_tokens_from_cookies
from api.main import app
from api.models import TokenData, SpotifyItemResponse, SpotifyItem, TopEmotionsResponse
from api.services.insights_service import InsightsService, InsightsServiceException
from api.services.music.spotify_data_service import SpotifyDataService, SpotifyDataServiceNotFoundException, \
    SpotifyDataServiceException
from api.settings import Settings

TEST_FRONTEND_URL = "http://test-frontend-url.com"
MOCK_OAUTH_STATE = "12345"


@pytest.fixture
def mock_spotify_data_service() -> MagicMock:
    return MagicMock(spec=SpotifyDataService)


@pytest.fixture
def mock_insights_service() -> MagicMock:
    return MagicMock(spec=InsightsService)


@pytest.fixture
def mock_settings() -> MagicMock:
    mock = MagicMock(spec=Settings)
    mock.frontend_url = TEST_FRONTEND_URL
    return mock


@pytest.fixture
def mock_request_tokens() -> MagicMock:
    mock = MagicMock(spec=TokenData)
    mock.access_token = "access"
    mock.refresh_token = "refresh"
    return mock


@pytest.fixture
def mock_response_tokens() -> MagicMock:
    mock = MagicMock(spec=TokenData)
    mock.access_token = "new_access"
    mock.refresh_token = "new_refresh"
    return mock


@pytest.fixture
def client(mock_request_tokens) -> TestClient:
    app.dependency_overrides[get_tokens_from_cookies] = lambda: mock_request_tokens
    return TestClient(app, follow_redirects=False)


@pytest.fixture
def mock_item_factory():
    def _create(item_id: str):
        mock = MagicMock(spec=SpotifyItem)
        mock.model_dump.return_value = {"id": item_id}
        return mock

    return _create


@pytest.fixture
def mock_item_response(mock_item_factory, mock_response_tokens) -> MagicMock:
    mock = MagicMock(spec=SpotifyItemResponse)
    mock.data = mock_item_factory(item_id="1")
    mock.tokens = mock_response_tokens
    return mock


@pytest.fixture
def mock_items_response(mock_item_factory, mock_response_tokens) -> MagicMock:
    mock = MagicMock(spec=SpotifyItemResponse)
    mock_items = [mock_item_factory(item_id=str(i)) for i in range(1, 6)]
    mock.data = mock_items
    mock.tokens = mock_response_tokens
    return mock


@pytest.fixture
def mock_emotions_response(mock_item_factory, mock_response_tokens) -> MagicMock:
    mock = MagicMock(spec=TopEmotionsResponse)
    mock_emotions = [mock_item_factory(item_id=str(i)) for i in range(1, 6)]
    mock.top_emotions = mock_emotions
    mock.tokens = mock_response_tokens
    return mock


# -------------------- GET ARTIST BY ID -------------------- #
# 1. Test that /data/artists/{artist_id} returns 404 status code if Spotify artist not found.
# 2. Test that /data/artists/{artist_id} returns 500 status code if a SpotifyDataServiceException occurs.
# 3. Test that /data/artists/{artist_id} returns expected response.
def test_get_artist_by_id_404(client, mock_spotify_data_service):
    app.dependency_overrides[get_spotify_data_service] = lambda: mock_spotify_data_service
    mock_spotify_data_service.get_item_by_id.side_effect = SpotifyDataServiceNotFoundException("Test")

    res = client.get("/data/artists/1")

    assert res.status_code == 404 and "Could not find the requested item." in res.text


def test_get_artist_by_id_500(client, mock_spotify_data_service):
    app.dependency_overrides[get_spotify_data_service] = lambda: mock_spotify_data_service
    mock_spotify_data_service.get_item_by_id.side_effect = SpotifyDataServiceException("Test")

    res = client.get("/data/artists/1")

    assert res.status_code == 500 and "Something went wrong." in res.text


def test_get_artist_by_id_success(client, mock_spotify_data_service, mock_item_response):
    app.dependency_overrides[get_spotify_data_service] = lambda: mock_spotify_data_service
    mock_spotify_data_service.get_item_by_id.return_value = mock_item_response

    res = client.get("/data/artists/1")

    set_cookie_headers = res.headers.get("set-cookie")
    assert (
            res.status_code == 200 and
            res.json() == {"id": "1"} and
            "new_access" in set_cookie_headers and
            "new_refresh" in set_cookie_headers
    )


# -------------------- GET TRACK BY ID -------------------- #
# 1. Test that /data/tracks/{track_id} returns 404 status code if Spotify track not found.
# 2. Test that /data/tracks/{track_id} returns 500 status code if a SpotifyDataServiceException occurs.
# 3. Test that /data/tracks/{track_id} returns expected response.
def test_get_track_by_id_404(client, mock_spotify_data_service):
    app.dependency_overrides[get_spotify_data_service] = lambda: mock_spotify_data_service
    mock_spotify_data_service.get_item_by_id.side_effect = SpotifyDataServiceNotFoundException("Test")

    res = client.get("/data/tracks/1")

    assert res.status_code == 404 and "Could not find the requested item." in res.text


def test_get_track_by_id_500(client, mock_spotify_data_service):
    app.dependency_overrides[get_spotify_data_service] = lambda: mock_spotify_data_service
    mock_spotify_data_service.get_item_by_id.side_effect = SpotifyDataServiceException("Test")

    res = client.get("/data/tracks/1")

    assert res.status_code == 500 and "Something went wrong." in res.text


def test_get_track_by_id_success(client, mock_spotify_data_service, mock_item_response):
    app.dependency_overrides[get_spotify_data_service] = lambda: mock_spotify_data_service
    mock_spotify_data_service.get_item_by_id.return_value = mock_item_response

    res = client.get("/data/tracks/1")

    set_cookie_headers = res.headers.get("set-cookie")
    assert (
            res.status_code == 200 and
            res.json() == {"id": "1"} and
            "new_access" in set_cookie_headers and
            "new_refresh" in set_cookie_headers
    )


# -------------------- GET TOP ARTISTS -------------------- #
# 1. Test that /data/top-artists returns 500 status code if a SpotifyDataServiceException occurs.
# 2. Test that /data/top-artists returns expected response.
def test_get_top_artists_500(client, mock_spotify_data_service):
    app.dependency_overrides[get_spotify_data_service] = lambda: mock_spotify_data_service
    mock_spotify_data_service.get_top_items.side_effect = SpotifyDataServiceException("Test")

    res = client.get("/data/top-artists")

    assert res.status_code == 500 and "Something went wrong." in res.text


def test_get_top_artists_success(client, mock_spotify_data_service, mock_items_response):
    app.dependency_overrides[get_spotify_data_service] = lambda: mock_spotify_data_service
    mock_spotify_data_service.get_top_items.return_value = mock_items_response

    res = client.get("/data/top-artists")

    set_cookie_headers = res.headers.get("set-cookie")
    assert (
            res.status_code == 200 and
            res.json() == [{"id": "1"}, {"id": "2"}, {"id": "3"}, {"id": "4"}, {"id": "5"}] and
            "new_access" in set_cookie_headers and
            "new_refresh" in set_cookie_headers
    )


# -------------------- GET TOP TRACKS -------------------- #
# 1. Test that /data/top-tracks returns 500 status code if a SpotifyDataServiceException occurs.
# 2. Test that /data/top-tracks returns expected JSON.
# 3. Test that /data/top-tracks sets response cookies.
def test_get_top_tracks_500(client, mock_spotify_data_service):
    app.dependency_overrides[get_spotify_data_service] = lambda: mock_spotify_data_service
    mock_spotify_data_service.get_top_items.side_effect = SpotifyDataServiceException("Test")

    res = client.get("/data/top-tracks")

    assert res.status_code == 500 and "Something went wrong." in res.text


def test_get_top_tracks_success(client, mock_spotify_data_service, mock_items_response):
    app.dependency_overrides[get_spotify_data_service] = lambda: mock_spotify_data_service
    mock_spotify_data_service.get_top_items.return_value = mock_items_response

    res = client.get("/data/top-tracks")

    set_cookie_headers = res.headers.get("set-cookie")
    assert (
            res.status_code == 200 and
            res.json() == [{"id": "1"}, {"id": "2"}, {"id": "3"}, {"id": "4"}, {"id": "5"}] and
            "new_access" in set_cookie_headers and
            "new_refresh" in set_cookie_headers
    )

# -------------------- GET TOP EMOTIONS -------------------- #
# 1. Test that /data/top-emotions returns 500 status code if InsightsServiceException occurs.
# 2. Test that /data/top-emotions returns expected response.
def test_get_top_emotions_500(client, mock_insights_service, mock_emotions_response):
    app.dependency_overrides[get_insights_service] = lambda: mock_insights_service
    mock_insights_service.get_top_emotions.side_effect = InsightsServiceException("Test")
    client.cookies.set("access_token", "access")
    client.cookies.set("refresh_token", "refresh")

    res = client.get("/data/top-emotions")

    assert res.status_code == 500 and "Something went wrong." in res.text


def test_get_top_emotions_success(client, mock_insights_service, mock_emotions_response):
    app.dependency_overrides[get_insights_service] = lambda: mock_insights_service
    mock_insights_service.get_top_emotions.return_value = mock_emotions_response

    res = client.get("/data/top-emotions")

    set_cookie_headers = res.headers.get("set-cookie")
    assert (
            res.status_code == 200 and
            res.json() == [{"id": "1"}, {"id": "2"}, {"id": "3"}, {"id": "4"}, {"id": "5"}] and
            "new_access" in set_cookie_headers and
            "new_refresh" in set_cookie_headers
    )
