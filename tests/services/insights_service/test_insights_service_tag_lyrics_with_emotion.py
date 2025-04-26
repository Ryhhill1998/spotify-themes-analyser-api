from unittest.mock import AsyncMock
import pytest

from api.data_structures.models import (
    TokenData,
    LyricsResponse,
    SpotifyTrack,
    SpotifyTrackArtist,
    SpotifyImage, SpotifyItemResponse, EmotionalTagsResponse, Emotion, TaggedLyricsResponse
)
from api.services.analysis_service import AnalysisService, AnalysisServiceException
from api.services.insights_service import InsightsService, InsightsServiceException
from api.services.lyrics_service import LyricsService, LyricsServiceException
from api.services.music.spotify_data_service import SpotifyDataService, SpotifyDataServiceException

TEST_URL = "http://test-url.com"

# 1. Test that tag_lyrics_with_emotion raises InsightsServiceException if any of its dependency services fail.
# 2. Test that tag_lyrics_with_emotion raises InsightsServiceException if data validation fails.
# 3. Test that tag_lyrics_with_emotion returns a TaggedLyricsResponse object if data is valid.


@pytest.fixture
def mock_spotify_data_service() -> AsyncMock:
    return AsyncMock(spec=SpotifyDataService)


@pytest.fixture
def mock_lyrics_service() -> AsyncMock:
    return AsyncMock(spec=LyricsService)


@pytest.fixture
def mock_analysis_service() -> AsyncMock:
    return AsyncMock(spec=AnalysisService)


@pytest.fixture
def insights_service(mock_spotify_data_service, mock_lyrics_service, mock_analysis_service) -> InsightsService:
    return InsightsService(
        spotify_data_service=mock_spotify_data_service,
        lyrics_service=mock_lyrics_service,
        analysis_service=mock_analysis_service
    )


@pytest.fixture
def mock_request_tokens() -> TokenData:
    return TokenData(access_token="access", refresh_token="refresh")


@pytest.fixture
def mock_spotify_data(mock_request_tokens) -> SpotifyItemResponse:
    data = SpotifyTrack(
        id="1",
        name="Track 1",
        images=[
            SpotifyImage(height=640, width=640, url="http://image-url.com")
        ],
        spotify_url="http://spotify-test-url.com",
        artist=SpotifyTrackArtist(id="1", name=f"Artist 1"),
        release_date="01/01/1999",
        explicit=False,
        duration_ms=100,
        popularity=50
    )
    return SpotifyItemResponse(data=data, tokens=mock_request_tokens)


@pytest.fixture
def mock_lyrics_data() -> LyricsResponse:
    return LyricsResponse(track_id="1", artist_name="Artist 1", track_title="Track 1", lyrics="Lyrics for Track 1")


@pytest.fixture
def mock_analysis_data() -> EmotionalTagsResponse:
    return EmotionalTagsResponse(
        track_id="1",
        lyrics="Lyrics for Track 1",
        emotion=Emotion.SADNESS
    )


@pytest.mark.asyncio
async def test_tag_lyrics_with_emotion_spotify_data_service_failure(
        insights_service,
        mock_spotify_data_service,
        mock_request_tokens
):
    exception_message = "Test SpotifyDataService failure"
    mock_spotify_data_service.get_item_by_id.side_effect = SpotifyDataServiceException(exception_message)

    with pytest.raises(InsightsServiceException, match="Service failure") as e:
        await insights_service.tag_lyrics_with_emotion(track_id="1", emotion=Emotion.SADNESS, tokens=mock_request_tokens)

    assert exception_message in str(e)


@pytest.mark.asyncio
async def test_tag_lyrics_with_emotion_lyrics_service_failure(
        insights_service,
        mock_request_tokens,
        mock_spotify_data_service,
        mock_spotify_data,
        mock_lyrics_service
):
    mock_spotify_data_service.get_item_by_id.return_value = mock_spotify_data
    exception_message = "Test LyricsService failure"
    mock_lyrics_service.get_lyrics.side_effect = LyricsServiceException(exception_message)

    with pytest.raises(InsightsServiceException, match="Service failure") as e:
        await insights_service.tag_lyrics_with_emotion(track_id="1", emotion=Emotion.SADNESS, tokens=mock_request_tokens)

    assert exception_message in str(e)


@pytest.mark.asyncio
async def test_tag_lyrics_with_emotion_analysis_service_failure(
        insights_service,
        mock_request_tokens,
        mock_spotify_data_service,
        mock_spotify_data,
        mock_lyrics_service,
        mock_lyrics_data,
        mock_analysis_service
):
    mock_spotify_data_service.get_item_by_id.return_value = mock_spotify_data
    mock_lyrics_service.get_lyrics.return_value = mock_lyrics_data
    exception_message = "Test LyricsService failure"
    mock_analysis_service.get_emotional_tags.side_effect = AnalysisServiceException(exception_message)

    with pytest.raises(InsightsServiceException, match="Service failure") as e:
        await insights_service.tag_lyrics_with_emotion(track_id="1", emotion=Emotion.SADNESS, tokens=mock_request_tokens)

    assert exception_message in str(e)


@pytest.mark.parametrize("attr_name", ["id", "name", "artist"])
@pytest.mark.asyncio
async def test_tag_lyrics_with_emotion_spotify_data_validation_failure(
        insights_service,
        mock_spotify_data_service,
        mock_request_tokens,
        mock_spotify_data,
        attr_name
):
    """Spotify data should be missing id, name, artist or artist.name"""
    mock_spotify_data_service.get_item_by_id.return_value = mock_spotify_data
    setattr(mock_spotify_data.data, attr_name, None)

    with pytest.raises(InsightsServiceException, match="Data validation failure"):
        await insights_service.tag_lyrics_with_emotion(track_id="1", emotion=Emotion.SADNESS, tokens=mock_request_tokens)


@pytest.mark.parametrize("attr_name", ["track_id", "lyrics"])
@pytest.mark.asyncio
async def test_tag_lyrics_with_emotion_lyrics_data_validation_failure(
        insights_service,
        mock_spotify_data_service,
        mock_request_tokens,
        mock_spotify_data,
        mock_lyrics_service,
        mock_lyrics_data,
        attr_name
):
    mock_spotify_data_service.get_item_by_id.return_value = mock_spotify_data
    mock_lyrics_service.get_lyrics.return_value = mock_lyrics_data
    setattr(mock_lyrics_data, attr_name, None)

    with pytest.raises(InsightsServiceException, match="Data validation failure"):
        await insights_service.tag_lyrics_with_emotion(track_id="1", emotion=Emotion.SADNESS, tokens=mock_request_tokens)


@pytest.mark.asyncio
async def test_tag_lyrics_with_emotion_returns_expected_response(
        insights_service,
        mock_spotify_data_service,
        mock_request_tokens,
        mock_spotify_data,
        mock_lyrics_service,
        mock_lyrics_data,
        mock_analysis_service,
        mock_analysis_data
):
    mock_spotify_data_service.get_item_by_id.return_value = mock_spotify_data
    mock_lyrics_service.get_lyrics.return_value = mock_lyrics_data
    mock_analysis_service.get_emotional_tags.return_value = mock_analysis_data

    res = await insights_service.tag_lyrics_with_emotion(track_id="1", emotion=Emotion.SADNESS, tokens=mock_request_tokens)

    expected_response = TaggedLyricsResponse(
        lyrics_data=EmotionalTagsResponse(track_id="1", emotion=Emotion.SADNESS, lyrics="Lyrics for Track 1"),
        tokens=mock_spotify_data.tokens
    )
    assert res == expected_response
