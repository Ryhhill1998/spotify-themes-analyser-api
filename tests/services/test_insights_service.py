from unittest.mock import AsyncMock
import pytest

from api.models import SpotifyItemsResponse, SpotifyItem, TokenData, LyricsResponse, EmotionalProfile, \
    EmotionalAnalysis, SpotifyTrack, SpotifyArtist, SpotifyTrackArtist, TopEmotionsResponse, TopEmotion, \
    SpotifyItemImage
from api.services.analysis_service import AnalysisService, AnalysisServiceException
from api.services.insights_service import InsightsService, InsightsServiceException
from api.services.lyrics_service import LyricsService, LyricsServiceException
from api.services.music.spotify_data_service import SpotifyDataService, SpotifyDataServiceException

TEST_URL = "http://test-url.com"


# 1. Test that get_top_emotions raises InsightsServiceException if any of its dependency services fail.
# 2. Test that get_top_emotions raises InsightsServiceException if data validation fails.
# 3. Test that get_top_emotions returns a TopEmotionsResponse object if data is valid.


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
def mock_tokens() -> TokenData:
    return TokenData(access_token="access", refresh_token="refresh")


@pytest.fixture
def mock_spotify_data(mock_tokens) -> SpotifyItemsResponse:
    data = [
        SpotifyTrack(
            id="0",
            name=f"Track 0",
            images=[
                SpotifyItemImage(height=640, width=640, url="http://image-url.com")
            ],
            spotify_url="http://spotify-test-url.com",
            artist=SpotifyTrackArtist(id="0", name=f"Artist 0"),
            release_date="01/01/1999",
            explicit=False,
            duration_ms=100,
            popularity=50
        ),
        SpotifyTrack(
            id="1",
            name=f"Track 0",
            images=[
                SpotifyItemImage(height=640, width=640, url="http://image-url.com")
            ],
            spotify_url="http://spotify-test-url.com",
            artist=SpotifyTrackArtist(id="1", name=f"Artist 1"),
            release_date="01/01/1999",
            explicit=False,
            duration_ms=100,
            popularity=50
        )
    ]
    return SpotifyItemsResponse(data=data, tokens=mock_tokens)


@pytest.fixture
def mock_lyrics_data() -> list[LyricsResponse]:
    return [
        LyricsResponse(track_id="1", artist_name="Artist 0", track_title="Track 0", lyrics="Lyrics for Track 0"),
        LyricsResponse(track_id="2", artist_name="Artist 1", track_title="Track 1", lyrics="Lyrics for Track 1"),
    ]


@pytest.fixture
def mock_analysis_data() -> list[EmotionalProfile]:
    return [
        EmotionalProfile(
            track_id="1",
            lyrics="Lyrics for Track 0",
            emotional_analysis=EmotionalAnalysis(
                joy=0.2,
                sadness=0.1,
                anger=0.05,
                fear=0,
                love=0,
                hope=0.05,
                nostalgia=0.04,
                loneliness=0.02,
                confidence=0.02,
                despair=0,
                excitement=0.01,
                mystery=0.01,
                defiance=0.2,
                gratitude=0.15,
                spirituality=0.15
            )
        ),
        EmotionalProfile(
            track_id="2",
            lyrics="Lyrics for Track 1",
            emotional_analysis=EmotionalAnalysis(
                joy=0,
                sadness=0.15,
                anger=0.05,
                fear=0,
                love=0,
                hope=0.05,
                nostalgia=0.24,
                loneliness=0.02,
                confidence=0.02,
                despair=0,
                excitement=0.01,
                mystery=0.06,
                defiance=0.3,
                gratitude=0,
                spirituality=0.1
            )
        )
    ]


@pytest.mark.asyncio
async def test_get_top_emotions_spotify_data_service_failure(insights_service, mock_spotify_data_service, mock_tokens):
    exception_message = "Test SpotifyDataService failure"
    mock_spotify_data_service.get_top_items.side_effect = SpotifyDataServiceException(exception_message)

    with pytest.raises(InsightsServiceException, match="Service failure") as e:
        await insights_service.get_top_emotions(mock_tokens)

    assert exception_message in str(e)


@pytest.mark.asyncio
async def test_get_top_emotions_lyrics_service_failure(
        insights_service,
        mock_spotify_data_service,
        mock_tokens,
        mock_spotify_data,
        mock_lyrics_service
):
    mock_spotify_data_service.get_top_items.return_value = mock_spotify_data
    exception_message = "Test LyricsService failure"
    mock_lyrics_service.get_lyrics_list.side_effect = LyricsServiceException(exception_message)

    with pytest.raises(InsightsServiceException, match="Service failure") as e:
        await insights_service.get_top_emotions(mock_tokens)

    assert exception_message in str(e)


@pytest.mark.asyncio
async def test_get_top_emotions_analysis_service_failure(
        insights_service,
        mock_spotify_data_service,
        mock_tokens,
        mock_spotify_data,
        mock_lyrics_service,
        mock_lyrics_data,
        mock_analysis_service
):
    mock_spotify_data_service.get_top_items.return_value = mock_spotify_data
    mock_lyrics_service.get_lyrics_list.return_value = mock_lyrics_data
    exception_message = "Test AnalysisService failure"
    mock_analysis_service.get_emotional_profiles.side_effect = AnalysisServiceException(exception_message)

    with pytest.raises(InsightsServiceException, match="Service failure") as e:
        await insights_service.get_top_emotions(mock_tokens)

    assert exception_message in str(e)


@pytest.mark.parametrize("attr_name", ["id", "name", "artist"])
@pytest.mark.asyncio
async def test_get_top_emotions_spotify_data_validation_failure(
        insights_service,
        mock_spotify_data_service,
        mock_tokens,
        mock_spotify_data,
        attr_name
):
    """Spotify data should be missing id, name, artist or artist.name"""
    mock_spotify_data_service.get_top_items.return_value = mock_spotify_data
    setattr(mock_spotify_data.data[0], attr_name, None)

    with pytest.raises(InsightsServiceException, match="Data validation failure"):
        await insights_service.get_top_emotions(mock_tokens)


@pytest.mark.parametrize("attr_name", ["track_id", "lyrics"])
@pytest.mark.asyncio
async def test_get_top_emotions_lyrics_data_validation_failure(
        insights_service,
        mock_spotify_data_service,
        mock_tokens,
        mock_spotify_data,
        mock_lyrics_service,
        mock_lyrics_data,
        attr_name
):
    mock_spotify_data_service.get_top_items.return_value = mock_spotify_data
    mock_lyrics_service.get_lyrics_list.return_value = mock_lyrics_data
    setattr(mock_lyrics_data[0], attr_name, None)

    with pytest.raises(InsightsServiceException, match="Data validation failure"):
        await insights_service.get_top_emotions(mock_tokens)


@pytest.mark.asyncio
async def test_get_top_emotions_analysis_data_validation_failure(
        insights_service,
        mock_spotify_data_service,
        mock_tokens,
        mock_spotify_data,
        mock_lyrics_service,
        mock_lyrics_data,
        mock_analysis_service,
        mock_analysis_data
):
    mock_spotify_data_service.get_top_items.return_value = mock_spotify_data
    mock_lyrics_service.get_lyrics_list.return_value = mock_lyrics_data
    mock_analysis_service.get_emotional_profiles.return_value = mock_analysis_data
    setattr(mock_analysis_data[0], "emotional_analysis", None)

    with pytest.raises(InsightsServiceException, match="Data validation failure"):
        await insights_service.get_top_emotions(mock_tokens)


@pytest.mark.asyncio
async def test_get_top_emotions_spotify_data_empty(
        insights_service,
        mock_spotify_data_service,
        mock_tokens,
        mock_spotify_data
):
    mock_spotify_data_service.get_top_items.return_value = mock_spotify_data
    mock_spotify_data.data = []

    with pytest.raises(
            InsightsServiceException,
            match="No top tracks found. Cannot proceed further with analysis."
    ):
        await insights_service.get_top_emotions(mock_tokens)


@pytest.mark.asyncio
async def test_get_top_emotions_lyrics_data_empty(
        insights_service,
        mock_spotify_data_service,
        mock_tokens,
        mock_spotify_data,
        mock_lyrics_service,
        mock_lyrics_data
):
    mock_spotify_data_service.get_top_items.return_value = mock_spotify_data
    mock_lyrics_service.get_lyrics_list.return_value = []

    with pytest.raises(
            InsightsServiceException,
            match="No lyrics found. Cannot proceed further with analysis."
    ):
        await insights_service.get_top_emotions(mock_tokens)


@pytest.mark.asyncio
async def test_get_top_emotions_analysis_data_empty(
        insights_service,
        mock_spotify_data_service,
        mock_tokens,
        mock_spotify_data,
        mock_lyrics_service,
        mock_lyrics_data,
        mock_analysis_service,
        mock_analysis_data
):
    mock_spotify_data_service.get_top_items.return_value = mock_spotify_data
    mock_lyrics_service.get_lyrics_list.return_value = mock_lyrics_data
    mock_analysis_service.get_emotional_profiles.return_value = []

    with pytest.raises(
            InsightsServiceException,
            match="No emotional profiles found. Cannot proceed further with analysis."
    ):
        await insights_service.get_top_emotions(mock_tokens)


@pytest.mark.parametrize("limit", [0, -1, -2, -100])
@pytest.mark.asyncio
async def test_get_top_emotions_invalid_limit(
        insights_service,
        mock_spotify_data_service,
        mock_tokens,
        mock_lyrics_service,
        mock_analysis_service,
        limit
):
    with pytest.raises(InsightsServiceException, match="Limit must be positive."):
        await insights_service.get_top_emotions(tokens=mock_tokens, limit=limit)


@pytest.mark.parametrize("limit", [5, 4, 3, 2, 1])
@pytest.mark.asyncio
async def test_get_top_emotions_returns_expected_response(
        insights_service,
        mock_spotify_data_service,
        mock_tokens,
        mock_spotify_data,
        mock_lyrics_service,
        mock_lyrics_data,
        mock_analysis_service,
        mock_analysis_data,
        limit
):
    mock_spotify_data_service.get_top_items.return_value = mock_spotify_data
    mock_lyrics_service.get_lyrics_list.return_value = mock_lyrics_data
    mock_analysis_service.get_emotional_profiles.return_value = mock_analysis_data

    top_emotions = [
        TopEmotion(name="defiance", percentage=0.25, track_id="2"),
        TopEmotion(name="nostalgia", percentage=0.14, track_id="2"),
        TopEmotion(name="sadness", percentage=0.12, track_id="2"),
        TopEmotion(name="spirituality", percentage=0.12, track_id="1"),
        TopEmotion(name="joy", percentage=0.1, track_id="1")
    ]

    expected_response = TopEmotionsResponse(top_emotions=top_emotions[:limit], tokens=mock_spotify_data.tokens)

    response = await insights_service.get_top_emotions(tokens=mock_tokens, limit=limit)

    assert response == expected_response
