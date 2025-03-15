import asyncio
from unittest.mock import AsyncMock, MagicMock
import pytest
from api.models import EmotionalProfileResponse, EmotionalProfile, EmotionalProfileRequest
from api.services.endpoint_requester import EndpointRequester
from api.services.analysis_service import AnalysisService, AnalysisServiceException

TEST_URL = "http://test-url.com"


# 1. Test that get_emotional_profiles returns [] if all get_emotional_profile tasks raise an AnalysisServiceException.
# 2. Test that get_emotional_profiles returns expected response.
# 3. Test that get_emotional_profiles calls get_emotional_profile expected number of times.


@pytest.fixture
def mock_endpoint_requester() -> AsyncMock:
    return AsyncMock(spec=EndpointRequester)


@pytest.fixture
def analysis_service(mock_endpoint_requester) -> AnalysisService:
    return AnalysisService(base_url=TEST_URL, endpoint_requester=mock_endpoint_requester)


@pytest.fixture
def mock_request_factory():
    def _create(track_id: str) -> EmotionalProfileRequest:
        return EmotionalProfileRequest(track_id=track_id, lyrics=f"Lyrics for Track {track_id}")

    return _create


@pytest.fixture
def mock_emotional_profile():
    return EmotionalProfile(
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


@pytest.fixture
def mock_response_factory(mock_emotional_profile):
    def _create(track_id: str) -> EmotionalProfileResponse:
        return EmotionalProfileResponse(
            track_id=track_id,
            lyrics=f"Lyrics for Track {track_id}",
            emotional_profile=mock_emotional_profile
        )

    return _create


@pytest.mark.asyncio
async def test_get_emotional_profiles_all_failures(analysis_service, mock_request_factory):
    analysis_service.get_emotional_profile = AsyncMock(side_effect=AnalysisServiceException)
    mock_requests = [mock_request_factory(str(i)) for i in range(1, 6)]

    res = await analysis_service.get_emotional_profiles(mock_requests)

    assert res == []


@pytest.mark.parametrize("exception_indices", [[], [0], [1], [2], [0, 1], [0, 2], [1, 2], [0, 1, 2]])
@pytest.mark.asyncio
async def test_get_emotional_profiles_returns_expected_response(
        analysis_service,
        mock_request_factory,
        mock_response_factory,
        exception_indices
):
    # ARRANGE
    mock_requests = [mock_request_factory(str(i)) for i in range(1, 4)]
    mock_task_list = [asyncio.Future(), asyncio.Future(), asyncio.Future()]
    analysis_service._create_emotional_profile_tasks = MagicMock(return_value=mock_task_list)

    mock_exception = AnalysisServiceException("Test")
    mock_responses = [mock_response_factory(str(i)) for i in range(1, 4)]
    for index in exception_indices:
        mock_responses[index] = mock_exception

    for index, response in enumerate(mock_responses):
        future_return_value = mock_task_list[index]

        if isinstance(response, Exception):
            future_return_value.set_exception(response)
        else:
            future_return_value.set_result(response)

    # ACT
    res = await analysis_service.get_emotional_profiles(mock_requests)

    # ASSERT
    full_response = [
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
            track_id="2",
            lyrics="Lyrics for Track 2",
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
            track_id="3",
            lyrics="Lyrics for Track 3",
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
    exception_indices_set = set(exception_indices)
    expected_response = [res for index, res in enumerate(full_response) if index not in exception_indices_set]
    assert res == expected_response


@pytest.mark.asyncio
async def test_get_emotional_profiles_calls_get_emotional_profile_expected_times(
        analysis_service,
        mock_request_factory,
        mock_response_factory
):
    mock_requests = [mock_request_factory(str(i)) for i in range(1, 6)]
    mock_response = [mock_response_factory(str(i)) for i in range(1)].pop()
    task = asyncio.Future()
    task.set_result(mock_response)
    analysis_service.get_emotional_profile = MagicMock(return_value=task)

    await analysis_service.get_emotional_profiles(mock_requests)

    assert analysis_service.get_emotional_profile.call_count == len(mock_requests)
