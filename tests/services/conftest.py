from unittest.mock import AsyncMock

import pytest

from api.services.endpoint_requester import EndpointRequester


@pytest.fixture
def mock_endpoint_requester() -> AsyncMock:
    return AsyncMock(spec=EndpointRequester)
