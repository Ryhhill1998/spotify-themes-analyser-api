from unittest.mock import AsyncMock
import pytest
from api.models import AnalysisRequest, TopEmotion
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
        {"track_id": "2", "emotional_profile": {"happiness": 0.6, "sadness": 0.4}}
    ]
