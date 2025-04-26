import pytest
from api.data_structures.models import EmotionalProfileResponse, EmotionalProfile, EmotionalProfileRequest
from api.services.endpoint_requester import EndpointRequesterException
from api.services.analysis_service import AnalysisServiceException

# 1. Test that get_emotional_profile raises AnalysisServiceException if data validation fails.
# 2. Test that get_emotional_profile raises AnalysisServiceException if API request fails.
# 3. Test that get_emotional_profile returns expected response.


@pytest.fixture
def mock_request() -> EmotionalProfileRequest:
    return EmotionalProfileRequest(track_id="1", lyrics="Lyrics for Track 1")


@pytest.fixture
def mock_response() -> dict:
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


@pytest.mark.parametrize("missing_field", ["track_id", "lyrics", "emotional_profile"])
@pytest.mark.asyncio
async def test_get_emotional_profile_data_validation_failure(
        analysis_service,
        mock_endpoint_requester,
        mock_request,
        mock_response,
        missing_field
):
    mock_response.pop(missing_field)
    mock_endpoint_requester.post.return_value = mock_response

    with pytest.raises(AnalysisServiceException, match="Failed to convert API response to EmotionalProfile object"):
        await analysis_service.get_emotional_profile(mock_request)


@pytest.mark.asyncio
async def test_get_emotional_profile_api_request_failure(analysis_service, mock_endpoint_requester, mock_request):
    mock_endpoint_requester.post.side_effect = EndpointRequesterException()

    with pytest.raises(AnalysisServiceException, match="Request to Analysis API failed"):
        await analysis_service.get_emotional_profile(mock_request)


@pytest.mark.asyncio
async def test_get_emotional_profile_data_success(
        analysis_service,
        mock_endpoint_requester,
        mock_request,
        mock_response
):
    mock_endpoint_requester.post.return_value = mock_response

    res = await analysis_service.get_emotional_profile(mock_request)

    expected_response = EmotionalProfileResponse(
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
    assert res == expected_response
