from unittest.mock import AsyncMock
import pytest

from api.models import SpotifyItemsResponse, SpotifyItem, TokenData, LyricsResponse, EmotionalProfile, EmotionalAnalysis
from api.services.analysis_service import AnalysisService
from api.services.insights_service import InsightsService
from api.services.lyrics_service import LyricsService
from api.services.music.spotify_data_service import SpotifyDataService

TEST_URL = "http://test-url.com"


# 1. Test that get_top_emotions raises InsightsServiceException if any of its dependency services fail.
# 2. Test that get_top_emotions raises InsightsServiceException if data validation fails.
# 3. Test that get_top_emotions returns a TopEmotionsResponse object if data is valid.


@pytest.fixture
def spotify_data_service() -> AsyncMock:
    return AsyncMock(spec=SpotifyDataService)


@pytest.fixture
def lyrics_service() -> AsyncMock:
    return AsyncMock(spec=LyricsService)


@pytest.fixture
def analysis_service() -> AsyncMock:
    return AsyncMock(spec=AnalysisService)


@pytest.fixture
def insights_service(spotify_data_service, lyrics_service, analysis_service) -> InsightsService:
    return InsightsService(
        spotify_data_service=spotify_data_service,
        lyrics_service=lyrics_service,
        analysis_service=analysis_service
    )


@pytest.fixture
def mock_spotify_data() -> SpotifyItemsResponse:
    data = [
        SpotifyItem(
            id="1",
            name="Item 1",
            images=[{"name": "Item 1 image", "url": "http://test.com/item-1.png"}],
            spotify_url="http://test.com/item-1"
        ),
        SpotifyItem(
            id="2",
            name="Item 2",
            images=[{"name": "Item 2 image", "url": "http://test.com/item-2.png"}],
            spotify_url="http://test.com/item-2"
        ),
    ]
    tokens = TokenData(access_token="access", refresh_token="refresh")

    return SpotifyItemsResponse(data=data, tokens=tokens)


@pytest.fixture
def mock_lyrics_response() -> list[LyricsResponse]:
    return [
        LyricsResponse(track_id="1", artist_name="Artist A", track_title="Song A", lyrics="Lyrics for Song A"),
        LyricsResponse(track_id="2", artist_name="Artist B", track_title="Song B", lyrics="Lyrics for Song B"),
    ]


@pytest.fixture
def mock_analysis_response() -> list[EmotionalProfile]:
    return [
        EmotionalProfile(
            track_id="1",
            lyrics="Lyrics for Song A",
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
            lyrics="Lyrics for Song B",
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
async def test_get_top_emotions_spotify_data_service_failure(insights_service):
    pass


@pytest.mark.asyncio
async def test_get_top_emotions_lyrics_service_failure(insights_service):
    pass


@pytest.mark.asyncio
async def test_get_top_emotions_analysis_service_failure(insights_service):
    pass


@pytest.mark.asyncio
async def test_get_top_emotions_spotify_data_validation_failure(insights_service):
    pass


@pytest.mark.asyncio
async def test_get_top_emotions_lyrics_data_validation_failure(insights_service):
    pass


@pytest.mark.asyncio
async def test_get_top_emotions_analysis_data_validation_failure(insights_service):
    pass


@pytest.mark.asyncio
async def test_get_top_emotions_returns_expected_response(insights_service):
    pass
