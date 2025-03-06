from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from api.services.endpoint_requester import EndpointRequester

TEST_URL = "http://test-url.com"
SUCCESS_RESPONSE = {"message": "success"}
ERROR_RESPONSE = "Bad Request"


@pytest.fixture
def mock_httpx_client() -> AsyncMock:
    mock = AsyncMock(spec=httpx.AsyncClient)
    return mock


@pytest.fixture
def endpoint_requester(mock_httpx_client) -> EndpointRequester:
    er = EndpointRequester(mock_httpx_client)
    return er


@pytest.fixture
def mock_response_success() -> MagicMock:
    expected_data = SUCCESS_RESPONSE
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = expected_data
    return mock_response


@pytest.fixture
def mock_response_failure() -> MagicMock:
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        message="Bad Request",
        request=MagicMock(),
        response=mock_response
    )
    return mock_response


@pytest.mark.parametrize("method", ["get", "post"])
@pytest.mark.asyncio
async def test_success_response(endpoint_requester, mock_httpx_client, mock_response_success, method):
    """Test GET and POST requests with 2XX status code responses return expected data"""
    mock_method = getattr(mock_httpx_client, method)
    mock_method.return_value = mock_response_success

    method_to_test = getattr(endpoint_requester, method)
    data = await method_to_test(TEST_URL)

    assert data == SUCCESS_RESPONSE


@pytest.mark.parametrize("method, extras", [("get", {"params": None}), ("post", {"data": None, "json": None})])
@pytest.mark.asyncio
async def test_client_interaction(endpoint_requester, mock_httpx_client, mock_response_success, method, extras):
    """Test GET and POST requests only call client get/post method once"""
    mock_method = getattr(mock_httpx_client, method)
    mock_method.return_value = mock_response_success
    method_to_test = getattr(endpoint_requester, method)

    await method_to_test(TEST_URL)

    mock_method.assert_called_once_with(url=TEST_URL, headers=None, timeout=None, **extras)


@pytest.mark.parametrize("method", ["get", "post"])
@pytest.mark.asyncio
async def test_failure(endpoint_requester, mock_httpx_client, mock_response_failure, method):
    """
    Test GET and POST requests with non-2XX status code responses raise HTTPStatusError and do not call json method on
    response
    """
    mock_method = getattr(mock_httpx_client, method)
    mock_method.return_value = mock_response_failure
    method_to_test = getattr(endpoint_requester, method)

    with pytest.raises(httpx.HTTPStatusError, match=ERROR_RESPONSE):
        await method_to_test(TEST_URL)

    mock_response_failure.json.assert_not_called()
