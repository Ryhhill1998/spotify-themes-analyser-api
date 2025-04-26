import pytest
from api.data_structures.models import EmotionalTagsRequest, EmotionalTagsResponse, Emotion
from api.services.endpoint_requester import EndpointRequesterException
from api.services.analysis_service import AnalysisServiceException

# 1. Test that get_emotional_tags raises AnalysisServiceException if data validation fails.
# 2. Test that get_emotional_tags raises AnalysisServiceException if API request fails.
# 3. Test that get_emotional_tags returns expected response.


@pytest.fixture
def mock_request() -> EmotionalTagsRequest:
    return EmotionalTagsRequest(track_id="1", lyrics="Lyrics for Track 1", emotion=Emotion.ANGER)


@pytest.fixture
def mock_response() -> dict:
    return {
        "track_id": "1",
        "lyrics": "Lyrics for Track 1",
        "emotion": "anger"
    }


@pytest.mark.parametrize("missing_field", ["track_id", "lyrics", "emotion"])
@pytest.mark.asyncio
async def test_get_emotional_tags_data_validation_failure(
        analysis_service,
        mock_endpoint_requester,
        mock_request,
        mock_response,
        missing_field
):
    mock_response.pop(missing_field)
    mock_endpoint_requester.post.return_value = mock_response

    with pytest.raises(AnalysisServiceException, match="Failed to convert API response to EmotionalTagsResponse object"):
        await analysis_service.get_emotional_tags(mock_request)



@pytest.mark.asyncio
async def test_get_emotional_profile_api_request_failure(analysis_service, mock_endpoint_requester, mock_request):
    mock_endpoint_requester.post.side_effect = EndpointRequesterException()

    with pytest.raises(AnalysisServiceException, match="Request to Analysis API failed"):
        await analysis_service.get_emotional_tags(mock_request)


@pytest.mark.asyncio
async def test_get_emotional_profile_data_success(
        analysis_service,
        mock_endpoint_requester,
        mock_request,
        mock_response
):
    mock_endpoint_requester.post.return_value = mock_response

    res = await analysis_service.get_emotional_tags(mock_request)

    expected_response = EmotionalTagsResponse(
        track_id="1",
        lyrics="Lyrics for Track 1",
        emotion=Emotion.ANGER
    )
    assert res == expected_response
