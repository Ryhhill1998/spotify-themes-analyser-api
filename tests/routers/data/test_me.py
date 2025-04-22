from unittest.mock import MagicMock

import pytest

from api.data_structures.models import TopEmotionsResponse, SpotifyItemResponse
from api.services.insights_service import InsightsServiceException
from api.services.music.spotify_data_service import SpotifyDataServiceException

BASE_URL = "/data/me/top"


@pytest.fixture
def mock_items_response(mock_item_factory, mock_response_tokens) -> MagicMock:
    mock = MagicMock(spec=SpotifyItemResponse)
    mock_items = [mock_item_factory(item_id=str(i)) for i in range(1, 6)]
    mock.data = mock_items
    mock.tokens = mock_response_tokens
    return mock


# -------------------- GET TOP ARTISTS -------------------- #
# 1. Test that /data/top-artists returns 500 status code if a SpotifyDataServiceException occurs.
# 2. Test that /data/top-artists returns expected response.
def test_get_top_artists_500(client, mock_spotify_data_service):
    mock_spotify_data_service.get_top_items.side_effect = SpotifyDataServiceException("Test")

    res = client.get(f"{BASE_URL}/artists")

    assert res.status_code == 500 and res.json() == {"detail": "Failed to retrieve the user's top items"}


def test_get_top_artists_success(client, mock_spotify_data_service, mock_items_response):
    mock_spotify_data_service.get_top_items.return_value = mock_items_response

    res = client.get(f"{BASE_URL}/artists")

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
    mock_spotify_data_service.get_top_items.side_effect = SpotifyDataServiceException("Test")

    res = client.get(f"{BASE_URL}/tracks")

    assert res.status_code == 500 and res.json() == {"detail": "Failed to retrieve the user's top items"}


def test_get_top_tracks_success(client, mock_spotify_data_service, mock_items_response):
    mock_spotify_data_service.get_top_items.return_value = mock_items_response

    res = client.get(f"{BASE_URL}/tracks")

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
@pytest.fixture
def mock_emotions_response(mock_item_factory, mock_response_tokens) -> MagicMock:
    mock = MagicMock(spec=TopEmotionsResponse)
    mock_emotions = [mock_item_factory(item_id=str(i)) for i in range(1, 6)]
    mock.top_emotions = mock_emotions
    mock.tokens = mock_response_tokens
    return mock


def test_get_top_emotions_500(client, mock_insights_service, mock_emotions_response):
    mock_insights_service.get_top_emotions.side_effect = InsightsServiceException("Test")

    res = client.get(f"{BASE_URL}/emotions")

    assert res.status_code == 500 and res.json() == {"detail": "Failed to retrieve the user's top emotions"}


def test_get_top_emotions_success(client, mock_insights_service, mock_emotions_response):
    mock_insights_service.get_top_emotions.return_value = mock_emotions_response

    res = client.get(f"{BASE_URL}/emotions")

    set_cookie_headers = res.headers.get("set-cookie")
    assert (
            res.status_code == 200 and
            res.json() == [{"id": "1"}, {"id": "2"}, {"id": "3"}, {"id": "4"}, {"id": "5"}] and
            "new_access" in set_cookie_headers and
            "new_refresh" in set_cookie_headers
    )
