from unittest.mock import MagicMock

import pytest
from starlette.testclient import TestClient

from api.dependencies import get_tokens_from_cookies, get_spotify_data_service, get_insights_service
from api.main import app
from api.data_structures.models import TokenData, SpotifyItemResponse
from api.services.insights_service import InsightsService
from api.services.music.spotify_data_service import SpotifyDataService


@pytest.fixture
def mock_spotify_data_service() -> MagicMock:
    return MagicMock(spec=SpotifyDataService)


@pytest.fixture
def mock_insights_service() -> MagicMock:
    return MagicMock(spec=InsightsService)


@pytest.fixture
def mock_response_tokens() -> MagicMock:
    mock = MagicMock(spec=TokenData)
    mock.access_token = "new_access"
    mock.refresh_token = "new_refresh"
    return mock


@pytest.fixture
def client(mock_request_tokens, mock_spotify_data_service, mock_insights_service) -> TestClient:
    app.dependency_overrides[get_tokens_from_cookies] = lambda: mock_request_tokens
    app.dependency_overrides[get_spotify_data_service] = lambda: mock_spotify_data_service
    app.dependency_overrides[get_insights_service] = lambda: mock_insights_service
    return TestClient(app, follow_redirects=False)


@pytest.fixture
def mock_item_factory():
    def _create(item_id: str):
        mock = MagicMock()
        mock.model_dump.return_value = {"id": item_id}
        return mock

    return _create


@pytest.fixture
def mock_item_response(mock_item_factory, mock_response_tokens) -> MagicMock:
    mock = MagicMock(spec=SpotifyItemResponse)
    mock.data = mock_item_factory(item_id="1")
    mock.tokens = mock_response_tokens
    return mock
