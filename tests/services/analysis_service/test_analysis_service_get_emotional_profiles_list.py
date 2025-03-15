from unittest.mock import AsyncMock
import pytest
from api.models import EmotionalProfileResponse, EmotionalProfile, EmotionalProfileRequest
from api.services.endpoint_requester import EndpointRequester, EndpointRequesterException
from api.services.analysis_service import AnalysisService

TEST_URL = "http://test-url.com"


# 1. Test that get_emotional_profiles raises AnalysisServiceNotFoundException if data == []
# 2. Test that get_emotional_profiles raises AnalysisServiceException if data validation fails.
# 3. Test that get_emotional_profiles raises AnalysisServiceException if API request fails.
# 4. Test that get_emotional_profiles returns a list of EmotionalProfile objects if API response is valid.


@pytest.fixture
def mock_endpoint_requester() -> AsyncMock:
    return AsyncMock(spec=EndpointRequester)


@pytest.fixture
def analysis_service(mock_endpoint_requester) -> AnalysisService:
    return AnalysisService(base_url=TEST_URL, endpoint_requester=mock_endpoint_requester)


@pytest.fixture
def mock_emotional_profile_requests() -> list[EmotionalProfileRequest]:
    return [
        EmotionalProfileRequest(track_id="1", lyrics="Lyrics for Track 1"),
        EmotionalProfileRequest(track_id="2", lyrics="Lyrics for Track 2"),
    ]


@pytest.fixture
def mock_emotional_profiles_list_response() -> dict:
    return {
        "track_id": "1",
        "lyrics": "Lyrics for Track 1",
        "emotional_profile": {
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
async def test_get_emotional_profiles_list_empty_response(
        analysis_service,
        mock_endpoint_requester,
        mock_emotional_profile_requests
):
    """Test that an empty API response returns an empty list."""

    # API returns empty list
    mock_endpoint_requester.post.return_value = []

    emotional_profiles = await analysis_service.get_emotional_profiles_list(mock_emotional_profile_requests)

    assert emotional_profiles == []


@pytest.mark.parametrize("missing_field", ["track_id", "lyrics", "emotional_profile"])
@pytest.mark.asyncio
async def test_get_emotional_profiles_list_invalid_response(
        analysis_service,
        mock_endpoint_requester,
        mock_emotional_profile_requests,
        mock_emotional_profiles_list_response,
        missing_field
):
    """Test that invalid API response structure is not returned in results."""

    # remove missing_field key from mock_response_data to simulate invalid API response
    mock_emotional_profiles_list_response.pop(missing_field)
    mock_endpoint_requester.post.return_value = mock_emotional_profiles_list_response

    res = await analysis_service.get_emotional_profiles_list(mock_emotional_profile_requests)

    assert res == []


@pytest.mark.asyncio
async def test_get_emotional_profiles_list_api_request_failure(
        analysis_service,
        mock_endpoint_requester,
        mock_emotional_profile_requests
):
    """Test that an empty API response raises a AnalysisServiceException."""

    mock_endpoint_requester.post.side_effect = EndpointRequesterException()

    res = await analysis_service.get_emotional_profiles_list(mock_emotional_profile_requests)

    assert res == []


@pytest.mark.asyncio
async def test_get_emotional_profiles_list_valid_response(
        analysis_service,
        mock_endpoint_requester,
        mock_emotional_profile_requests,
        mock_emotional_profiles_list_response
):
    """Test that get_analysis_list correctly converts API response to AnalysisResponse objects."""

    expected_analysis_list = [
        EmotionalProfileResponse(
            track_id="1",
            lyrics="Lyrics for Track 1",
            emotional_profile=EmotionalProfile(
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
        EmotionalProfileResponse(
            track_id="1",
            lyrics="Lyrics for Track 1",
            emotional_profile=EmotionalProfile(
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
        )
    ]

    mock_endpoint_requester.post.return_value = mock_emotional_profiles_list_response

    analysis_list = await analysis_service.get_emotional_profiles_list(mock_emotional_profile_requests)

    assert analysis_list == expected_analysis_list and mock_endpoint_requester.post.call_count == 2
