from unittest.mock import AsyncMock
import pytest
from api.models import AnalysisRequest, Emotion
from api.services.endpoint_requester import EndpointRequester
from api.services.analysis_service import AnalysisService, AnalysisServiceException

TEST_URL = "http://test-url.com"


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
        {"track_id": "1", "emotional_profile": {"happiness": 0.8, "sadness": 0.2}},
        {"track_id": "2", "emotional_profile": {"happiness": 0.6, "sadness": 0.4}},
    ]


@pytest.mark.parametrize("limit", [1, 2])
@pytest.mark.asyncio
async def test_get_top_emotions_valid_response(
        analysis_service,
        endpoint_requester,
        mock_analysis_requests,
        mock_response_data,
        limit
):
    """Test that get_top_emotions correctly processes API response and returns top emotions."""

    expected_emotions = [
        Emotion(name="happiness", percentage=0.7, track_id="1"),
        Emotion(name="sadness", percentage=0.3, track_id="2")
    ]

    endpoint_requester.post.return_value = mock_response_data

    top_emotions = await analysis_service.get_top_emotions(mock_analysis_requests, limit=limit)

    assert top_emotions == expected_emotions[:limit]
    endpoint_requester.post.assert_called_once()


@pytest.mark.parametrize("missing_field", ["track_id", "emotional_profile"])
@pytest.mark.asyncio
async def test_get_top_emotions_invalid_response(
        analysis_service,
        endpoint_requester,
        mock_analysis_requests,
        mock_response_data,
        missing_field
):
    """Test that missing fields in API response raises AnalysisServiceException."""

    mock_response_data[0].pop(missing_field)

    endpoint_requester.post.return_value = mock_response_data

    with pytest.raises(AnalysisServiceException, match="Failed to process API response"):
        await analysis_service.get_top_emotions(mock_analysis_requests)


@pytest.mark.asyncio
async def test_get_top_emotions_invalid_percentage_type(
        analysis_service,
        endpoint_requester,
        mock_analysis_requests,
        mock_response_data
):
    """Test that incorrect data types for percentages raise AnalysisServiceException."""

    mock_response_data[0]["emotional_profile"] = {"happiness": "invalid_value"}

    endpoint_requester.post.return_value = mock_response_data

    with pytest.raises(AnalysisServiceException, match="Failed to process API response"):
        await analysis_service.get_top_emotions(mock_analysis_requests)


@pytest.mark.asyncio
async def test_get_top_emotions_empty_response(analysis_service, endpoint_requester, mock_analysis_requests):
    """Test that an empty API response returns an empty list."""

    endpoint_requester.post.return_value = []

    top_emotions = await analysis_service.get_top_emotions(mock_analysis_requests)

    assert top_emotions == []  # Should return empty list, not raise an exception
