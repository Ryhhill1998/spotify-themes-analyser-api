from unittest.mock import AsyncMock

import pytest

from api.services.analysis_service import AnalysisService
from api.services.insights_service import InsightsService
from api.services.lyrics_service import LyricsService
from api.services.music.spotify_data_service import SpotifyDataService


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
