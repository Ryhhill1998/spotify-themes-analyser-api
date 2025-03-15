from unittest.mock import AsyncMock
import pytest
from api.models import LyricsRequest, LyricsResponse
from api.services.endpoint_requester import EndpointRequester, EndpointRequesterException
from api.services.lyrics_service import LyricsService, LyricsServiceException

TEST_URL = "http://test-url.com"

# 1. Test that get_lyrics_list raises LyricsServiceNotFoundException if data == []
# 2. Test that get_lyrics_list raises LyricsServiceException if data validation fails.
# 3. Test that get_lyrics_list raises LyricsServiceException if API request fails.
# 4. Test that get_lyrics_list returns a list of LyricsResponse objects if API response is valid.


@pytest.fixture
def mock_endpoint_requester() -> AsyncMock:
    return AsyncMock(spec=EndpointRequester)


@pytest.fixture
def lyrics_service(mock_endpoint_requester) -> LyricsService:
    return LyricsService(base_url=TEST_URL, endpoint_requester=mock_endpoint_requester)


@pytest.fixture
def mock_lyrics_requests() -> list[LyricsRequest]:
    return [
        LyricsRequest(track_id="1", artist_name="Artist 1", track_title="Track 1"),
        LyricsRequest(track_id="2", artist_name="Artist 2", track_title="Track 2"),
    ]


@pytest.fixture
def mock_response_data() -> list[dict[str, str]]:
    return [
        {"track_id": "1", "artist_name": "Artist 1", "track_title": "Track 1", "lyrics": "Lyrics for Track 1"},
        {"track_id": "2", "artist_name": "Artist 2", "track_title": "Track 2", "lyrics": "Lyrics for Track 2"},
    ]



@pytest.mark.asyncio
async def test_get_lyrics_list_empty_response(lyrics_service, endpoint_requester, mock_lyrics_requests):
    """Test that an empty API response returns an empty list."""

    # API returns empty list
    endpoint_requester.post.return_value = []

    lyrics_list = await lyrics_service.get_lyrics_list(mock_lyrics_requests)

    assert lyrics_list == []


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

    with pytest.raises(LyricsServiceException, match="Failed to convert API response to LyricsResponse object"):
        await lyrics_service.get_lyrics_list(mock_lyrics_requests)


@pytest.mark.asyncio
async def test_get_lyrics_list_api_request_failure(lyrics_service, endpoint_requester, mock_lyrics_requests):
    """Test that an empty API response raises a LyricsServiceException."""

    endpoint_requester.post.side_effect = EndpointRequesterException()

    with pytest.raises(LyricsServiceException, match="Request to Lyrics API failed"):
        await lyrics_service.get_lyrics_list(mock_lyrics_requests)


@pytest.mark.asyncio
async def test_get_lyrics_list_valid_response(
        lyrics_service,
        endpoint_requester,
        mock_lyrics_requests,
        mock_response_data
):
    """Test that get_lyrics_list correctly converts API response to LyricsResponse objects."""

    expected_lyrics_list = [
        LyricsResponse(track_id="1", artist_name="Artist 1", track_title="Track 1", lyrics="Lyrics for Track 1"),
        LyricsResponse(track_id="2", artist_name="Artist 2", track_title="Track 2", lyrics="Lyrics for Track 2"),
    ]

    endpoint_requester.post.return_value = mock_response_data

    lyrics_list = await lyrics_service.get_lyrics_list(mock_lyrics_requests)

    assert lyrics_list == expected_lyrics_list
    endpoint_requester.post.assert_called_once_with(
        url=f"{TEST_URL}/lyrics",
        json_data=[
            {"track_id": "1", "artist_name": "Artist 1", "track_title": "Track 1"},
            {"track_id": "2", "artist_name": "Artist 2", "track_title": "Track 2"},
        ],
        timeout=None
    )
