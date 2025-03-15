from unittest.mock import AsyncMock
import pytest
from api.models import EmotionalProfileResponse, EmotionalProfile, EmotionalProfileRequest
from api.services.endpoint_requester import EndpointRequester, EndpointRequesterException
from api.services.analysis_service import AnalysisService, AnalysisServiceException

TEST_URL = "http://test-url.com"

# 1. Test that get_emotional_profile raises AnalysisServiceException if data validation fails.
# 2. Test that get_emotional_profile raises AnalysisServiceException if API request fails.
# 3. Test that get_emotional_profile returns expected response.


@pytest.fixture
def mock_endpoint_requester() -> AsyncMock:
    return AsyncMock(spec=EndpointRequester)


@pytest.fixture
def analysis_service(mock_endpoint_requester) -> AnalysisService:
    return AnalysisService(base_url=TEST_URL, endpoint_requester=mock_endpoint_requester)


@pytest.fixture
def mock_request() -> EmotionalProfileRequest:
    return EmotionalProfileRequest(track_id="1", lyrics="Lyrics for Track 1")


@pytest.fixture
def mock_response() -> dict:
    return {
        "track_id": "1",
        "lyrics": "Lyrics for Track 1",
        "emotional_analysis": {
            "joy": 0.2,
            "sadness": 0.1,
            "anger": 0.05,
            "fear": 0,
            "love": 0,
            "hope": 0.05,
            "nostalgia": 0.04,
            "loneliness": 0.02,
            "confidence": 0.02,
            "despair": 0,
            "excitement": 0.01,
            "mystery": 0.01,
            "defiance": 0.2,
            "gratitude": 0.15,
            "spirituality": 0.15
        }
    }


@pytest.mark.asyncio
async def test_get_emotional_profile_data_validation_failure():
    pass


@pytest.mark.asyncio
async def test_get_emotional_profile_api_request_failure():
    pass


@pytest.mark.asyncio
async def test_get_emotional_profile_data_success():
    pass
