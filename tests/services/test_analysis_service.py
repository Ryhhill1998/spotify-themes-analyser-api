from unittest.mock import AsyncMock
import pytest
from api.models import AnalysisRequest, TopEmotion, EmotionalProfile, EmotionalAnalysis
from api.services.endpoint_requester import EndpointRequester, EndpointRequesterException
from api.services.analysis_service import AnalysisService, AnalysisServiceException

TEST_URL = "http://test-url.com"

# 1. Test that get_emotional_profiles raises AnalysisServiceNotFoundException if data == []
# 2. Test that get_emotional_profiles raises AnalysisServiceException if data validation fails.
# 3. Test that get_emotional_profiles raises AnalysisServiceException if API request fails.
# 4. Test that get_emotional_profiles returns a list of EmotionalProfile objects if API response is valid.


@pytest.fixture
def endpoint_requester() -> AsyncMock:
    return AsyncMock(spec=EndpointRequester)


@pytest.fixture
def analysis_service(endpoint_requester) -> AnalysisService:
    return AnalysisService(base_url=TEST_URL, endpoint_requester=endpoint_requester)


@pytest.fixture
def mock_analysis_requests() -> list[AnalysisRequest]:
    return [
        AnalysisRequest(track_id="1", lyrics="Lyrics for Song A"),
        AnalysisRequest(track_id="2", lyrics="Lyrics for Song B"),
    ]


@pytest.fixture
def mock_response_data() -> list[dict]:
    return [
        {
            "track_id": "1",
            "lyrics": "Lyrics for Song A",
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
        },
        {
            "track_id": "2",
            "lyrics": "Lyrics for Song B",
            "emotional_analysis": {
                "joy": 0, 
                "sadness": 0.15,
                "anger": 0.05,
                "fear": 0,
                "love": 0,
                "hope": 0.05,
                "nostalgia": 0.24,
                "loneliness": 0.02,
                "confidence": 0.02,
                "despair": 0,
                "excitement": 0.01,
                "mystery": 0.06,
                "defiance": 0.3,
                "gratitude": 0,
                "spirituality": 0.1
            }
        }
    ]



@pytest.mark.asyncio
async def test_get_analysis_list_empty_response(analysis_service, endpoint_requester, mock_analysis_requests):
    """Test that an empty API response raises a AnalysisServiceException."""

    # API returns empty list
    endpoint_requester.post.return_value = []

    with pytest.raises(AnalysisServiceException, match="No emotional profiles found for request"):
        await analysis_service.get_emotional_profiles(mock_analysis_requests)


@pytest.mark.parametrize("missing_field", ["track_id", "lyrics", "emotional_analysis"])
@pytest.mark.asyncio
async def test_get_analysis_list_invalid_response(
        analysis_service,
        endpoint_requester,
        mock_analysis_requests,
        mock_response_data,
        missing_field
):
    """Test that invalid API response structure raises AnalysisServiceException."""

    # remove missing_field key from mock_response_data to simulate invalid API response
    mock_response_data[0].pop(missing_field)

    endpoint_requester.post.return_value = mock_response_data

    with pytest.raises(AnalysisServiceException, match="Failed to convert API response to EmotionalProfile object"):
        await analysis_service.get_emotional_profiles(mock_analysis_requests)


@pytest.mark.asyncio
async def test_get_analysis_list_api_request_failure(analysis_service, endpoint_requester, mock_analysis_requests):
    """Test that an empty API response raises a AnalysisServiceException."""

    endpoint_requester.post.side_effect = EndpointRequesterException()

    with pytest.raises(AnalysisServiceException, match="Request to Analysis API failed"):
        await analysis_service.get_emotional_profiles(mock_analysis_requests)


@pytest.mark.asyncio
async def test_get_analysis_list_valid_response(
        analysis_service,
        endpoint_requester,
        mock_analysis_requests,
        mock_response_data
):
    """Test that get_analysis_list correctly converts API response to AnalysisResponse objects."""

    expected_analysis_list = [
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

    endpoint_requester.post.return_value = mock_response_data

    analysis_list = await analysis_service.get_emotional_profiles(mock_analysis_requests)

    assert analysis_list == expected_analysis_list
    endpoint_requester.post.assert_called_once_with(
        url=f"{TEST_URL}/emotional-profile",
        json_data=[
            {"track_id": "1", "lyrics": "Lyrics for Song A"},
            {"track_id": "2", "lyrics": "Lyrics for Song B"},
        ],
        timeout=None
    )

