from unittest.mock import MagicMock

import pytest

from api.data_structures.models import TaggedLyricsResponse
from api.services.insights_service import InsightsServiceException
from api.services.music.spotify_data_service import SpotifyDataServiceNotFoundException, SpotifyDataServiceException

BASE_URL = "/data/tracks"


# -------------------- GET TRACK BY ID -------------------- #
# 1. Test that /data/tracks/{track_id} returns 404 status code if Spotify track not found.
# 2. Test that /data/tracks/{track_id} returns 500 status code if a SpotifyDataServiceException occurs.
# 3. Test that /data/tracks/{track_id} returns expected response.
def test_get_track_by_id_404(client, mock_spotify_data_service):
    mock_spotify_data_service.get_item_by_id.side_effect = SpotifyDataServiceNotFoundException("Test")

    res = client.get(f"{BASE_URL}/1")

    assert res.status_code == 404 and res.json() == {"detail": "Could not find the requested item"}


def test_get_track_by_id_500(client, mock_spotify_data_service):
    mock_spotify_data_service.get_item_by_id.side_effect = SpotifyDataServiceException("Test")

    res = client.get(f"{BASE_URL}/1")

    assert res.status_code == 500 and res.json() == {"detail": "Failed to retrieve the requested item"}


def test_get_track_by_id_success(client, mock_spotify_data_service, mock_item_response):
    mock_spotify_data_service.get_item_by_id.return_value = mock_item_response

    res = client.get(f"{BASE_URL}/1")

    set_cookie_headers = res.headers.get("set-cookie")
    assert (
            res.status_code == 200 and
            res.json() == {"id": "1"} and
            "new_access" in set_cookie_headers and
            "new_refresh" in set_cookie_headers
    )


# -------------------- GET LYRICS TAGGED WITH EMOTION -------------------- #
# 1. Test that /tracks/{track_id}/lyrics/emotions/{emotion} returns 500 status code if InsightsServiceException occurs.
# 2. Test that /tracks/{track_id}/lyrics/emotions/{emotion} returns 422 status code if invalid emotion provided.
# 3. Test that /tracks/{track_id}/lyrics/emotions/{emotion} returns expected response.
@pytest.fixture
def mock_tagged_lyrics_response(mock_item_factory, mock_response_tokens) -> MagicMock:
    mock = MagicMock(spec=TaggedLyricsResponse)
    mock_tagged_lyrics = mock_item_factory(item_id=str(1))
    mock.lyrics_data = mock_tagged_lyrics
    mock.tokens = mock_response_tokens
    return mock


def test_get_lyrics_tagged_with_emotion_500(client, mock_insights_service):
    mock_insights_service.tag_lyrics_with_emotion.side_effect = InsightsServiceException("Test")

    res = client.get(f"{BASE_URL}/1/lyrics/emotional-tags/joy")

    assert res.status_code == 500 and res.json() == {"detail": "Failed to tag lyrics with requested emotion"}


def test_get_lyrics_tagged_with_emotion_422(client, mock_insights_service):
    mock_insights_service.tag_lyrics_with_emotion.side_effect = InsightsServiceException("Test")

    res = client.get(f"{BASE_URL}/1/lyrics/emotional-tags/blah")

    assert res.status_code == 422


def test_get_lyrics_tagged_with_emotion_success(client, mock_insights_service, mock_tagged_lyrics_response):
    mock_insights_service.tag_lyrics_with_emotion.return_value = mock_tagged_lyrics_response

    res = client.get(f"{BASE_URL}/1/lyrics/emotional-tags/joy")

    set_cookie_headers = res.headers.get("set-cookie")
    assert (
            res.status_code == 200 and
            res.json() == {"id": "1"} and
            "new_access" in set_cookie_headers and
            "new_refresh" in set_cookie_headers
    )
