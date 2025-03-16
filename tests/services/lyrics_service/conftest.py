import pytest

from api.services.lyrics_service import LyricsService

TEST_URL = "http://test-url.com"


@pytest.fixture
def lyrics_service(mock_endpoint_requester) -> LyricsService:
    return LyricsService(base_url=TEST_URL, endpoint_requester=mock_endpoint_requester)
