from unittest.mock import AsyncMock
import pytest
from api.models import LyricsRequest, LyricsResponse
from api.services.endpoint_requester import EndpointRequester
from api.services.lyrics_service import LyricsService, LyricsServiceException

TEST_URL = "http://test-url.com"


@pytest.fixture
def endpoint_requester() -> AsyncMock:
    return AsyncMock(spec=EndpointRequester)


@pytest.fixture
def lyrics_service(endpoint_requester) -> LyricsService:
    return LyricsService(base_url=TEST_URL, endpoint_requester=endpoint_requester)


@pytest.fixture
def mock_lyrics_requests() -> list[LyricsRequest]:
    return [
        LyricsRequest(track_id="1", artist_name="Artist A", track_title="Song A"),
        LyricsRequest(track_id="2", artist_name="Artist B", track_title="Song B"),
    ]


@pytest.fixture
def mock_response_data() -> list[dict[str, str]]:
    return [
        {"track_id": "1", "artist_name": "Artist A", "track_title": "Song A", "lyrics": "Lyrics for Song A"},
        {"track_id": "2", "artist_name": "Artist B", "track_title": "Song B", "lyrics": "Lyrics for Song B"},
    ]


@pytest.mark.asyncio
async def test_get_lyrics_list_valid_response(
        lyrics_service,
        endpoint_requester,
        mock_lyrics_requests,
        mock_response_data
):
    """Test that get_lyrics_list correctly converts API response to LyricsResponse objects."""

    expected_lyrics_list = [LyricsResponse(**entry) for entry in mock_response_data]

    endpoint_requester.post.return_value = mock_response_data

    lyrics_list = await lyrics_service.get_lyrics_list(mock_lyrics_requests)

    assert lyrics_list == expected_lyrics_list
    endpoint_requester.post.assert_called_once_with(
        url=f"{TEST_URL}/lyrics-list",
        json_data=[item.model_dump() for item in mock_lyrics_requests],
        timeout=None
    )


@pytest.mark.parametrize("missing_field", ["track_id", "artist_name", "track_title", "lyrics"])
@pytest.mark.asyncio
async def test_get_lyrics_list_invalid_response(
        lyrics_service,
        endpoint_requester,
        mock_lyrics_requests,
        mock_response_data,
        missing_field
):
    """Test that invalid API response structure raises LyricsServiceException."""

    # remove missing_field key from mock_response_data to simulate invalid API response
    mock_response_data[0].pop(missing_field)

    endpoint_requester.post.return_value = mock_response_data

    with pytest.raises(LyricsServiceException, match="Failed to convert API response"):
        await lyrics_service.get_lyrics_list(mock_lyrics_requests)


@pytest.mark.asyncio
async def test_get_lyrics_list_empty_response(lyrics_service, endpoint_requester, mock_lyrics_requests):
    """Test that an empty API response raises a LyricsServiceException."""

    # API returns empty list
    endpoint_requester.post.return_value = []

    with pytest.raises(LyricsServiceException, match="No lyrics found for request"):
        await lyrics_service.get_lyrics_list(mock_lyrics_requests)
