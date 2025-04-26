import pytest
from api.data_structures.models import LyricsRequest, LyricsResponse
from api.services.endpoint_requester import EndpointRequesterException, EndpointRequesterNotFoundException
from api.services.lyrics_service import LyricsServiceException, LyricsServiceNotFoundException

TEST_URL = "http://test-url.com"

# 1. Test that get_lyrics raises LyricsServiceException if data validation fails.
# 2. Test that get_lyrics raises LyricsServiceException if API request fails.
# 3. Test that get_lyrics returns expected response.


@pytest.fixture
def mock_request() -> LyricsRequest:
    return LyricsRequest(track_id="1", artist_name="Artist 1", track_title="Track 1")


@pytest.fixture
def mock_response() -> dict[str, str]:
    return {"track_id": "1", "artist_name": "Artist 1", "track_title": "Track 1", "lyrics": "Lyrics for Track 1"}


@pytest.mark.parametrize("missing_field", ["track_id", "artist_name", "track_title", "lyrics"])
@pytest.mark.asyncio
async def test_get_lyrics_data_validation_failure(
        lyrics_service,
        mock_endpoint_requester,
        mock_request,
        mock_response,
        missing_field
):
    """Test that invalid API response structure raises LyricsServiceException."""

    # remove missing_field key from mock_response_data to simulate invalid API response
    mock_response.pop(missing_field)

    mock_endpoint_requester.post.return_value = mock_response

    with pytest.raises(LyricsServiceException, match="Failed to convert API response to LyricsResponse object"):
        await lyrics_service.get_lyrics(mock_request)


@pytest.mark.asyncio
async def test_get_lyrics_api_request_not_found_failure(lyrics_service, mock_endpoint_requester, mock_request):
    """Test that an empty API response raises a LyricsServiceException."""

    mock_endpoint_requester.post.side_effect = EndpointRequesterNotFoundException()

    with pytest.raises(
            LyricsServiceNotFoundException,
            match=f"Requested lyrics not found for track_id: 1, artist_name: Artist 1, track_title: Track 1"
    ):
        await lyrics_service.get_lyrics(mock_request)


@pytest.mark.asyncio
async def test_get_lyrics_api_request_failure(lyrics_service, mock_endpoint_requester, mock_request):
    """Test that an empty API response raises a LyricsServiceException."""

    mock_endpoint_requester.post.side_effect = EndpointRequesterException()

    with pytest.raises(LyricsServiceException, match="Request to Lyrics API failed"):
        await lyrics_service.get_lyrics(mock_request)


@pytest.mark.asyncio
async def test_get_lyrics_success(
        lyrics_service,
        mock_endpoint_requester,
        mock_request,
        mock_response
):
    """Test that get_lyrics_list correctly converts API response to LyricsResponse objects."""

    mock_endpoint_requester.post.return_value = mock_response

    res = await lyrics_service.get_lyrics(mock_request)

    expected_response = LyricsResponse(
        track_id="1",
        artist_name="Artist 1",
        track_title="Track 1",
        lyrics="Lyrics for Track 1"
    )
    assert res == expected_response
    mock_endpoint_requester.post.assert_called_once_with(
        url=f"{TEST_URL}/lyrics",
        json_data={"track_id": "1", "artist_name": "Artist 1", "track_title": "Track 1"},
        timeout=None
    )
