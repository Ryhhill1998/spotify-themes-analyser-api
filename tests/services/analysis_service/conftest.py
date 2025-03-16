import pytest

from api.services.analysis_service import AnalysisService

TEST_URL = "http://test-url.com"


@pytest.fixture
def analysis_service(mock_endpoint_requester) -> AnalysisService:
    return AnalysisService(base_url=TEST_URL, endpoint_requester=mock_endpoint_requester)
