from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from api.services.endpoint_requester import EndpointRequester, EndpointRequesterException, \
    EndpointRequesterUnauthorisedException

TEST_URL = "http://test-url.com"
SUCCESS_RESPONSE = {"message": "success"}
ERROR_RESPONSE = "Bad Request"


@pytest.fixture
def mock_httpx_client() -> AsyncMock:
    return AsyncMock(spec=httpx.AsyncClient)


@pytest.fixture
def endpoint_requester(mock_httpx_client) -> EndpointRequester:
    return EndpointRequester(mock_httpx_client)


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
    mock_response.status_code = 400
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
    mock_httpx_client.request.return_value = mock_response_success

    method_to_test = getattr(endpoint_requester, method)
    data = await method_to_test(TEST_URL)

    assert data == SUCCESS_RESPONSE


@pytest.mark.parametrize("method", ["get", "post"])
@pytest.mark.asyncio
async def test_client_interaction(endpoint_requester, mock_httpx_client, mock_response_success, method):
    """Test GET and POST requests only call client get/post method once"""
    mock_httpx_client.request.return_value = mock_response_success
    method_to_test = getattr(endpoint_requester, method)

    await method_to_test(TEST_URL)

    mock_httpx_client.request.assert_called_once_with(
        method=method.upper(),
        url=TEST_URL,
        headers=None,
        params=None,
        data=None,
        json=None,
        timeout=None,
    )


@pytest.mark.parametrize("method", ["get", "post"])
@pytest.mark.asyncio
async def test_failure(endpoint_requester, mock_httpx_client, mock_response_failure, method):
    """
    Test GET and POST requests with non-2XX status code responses raise EndpointRequesterException and do not call json
    method on response
    """
    mock_httpx_client.request.return_value = mock_response_failure
    method_to_test = getattr(endpoint_requester, method)

    with pytest.raises(EndpointRequesterException):
        await method_to_test(TEST_URL)

    mock_response_failure.json.assert_not_called()


@pytest.mark.parametrize("method", ["get", "post"])
@pytest.mark.asyncio
async def test_401_error_raises_custom_unauthorised_exception(endpoint_requester, mock_httpx_client, method):
    """
    Test GET and POST requests with 401 status code responses raise EndpointRequesterUnauthorisedException
    """
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 401
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        message="Unauthorized",
        request=MagicMock(),
        response=mock_response
    )
    mock_httpx_client.request.return_value = mock_response
    method_to_test = getattr(endpoint_requester, method)

    with pytest.raises(EndpointRequesterUnauthorisedException):
        await method_to_test(TEST_URL)


@pytest.mark.parametrize("method", ["get", "post"])
@pytest.mark.asyncio
async def test_401_error_raises_custom_unauthorised_exception(endpoint_requester, mock_httpx_client, method):
    """
    Test GET and POST requests with 401 status code responses raise EndpointRequesterUnauthorisedException
    """
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 401
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        message="Unauthorized",
        request=MagicMock(),
        response=mock_response
    )
    mock_httpx_client.request.return_value = mock_response
    method_to_test = getattr(endpoint_requester, method)

    with pytest.raises(EndpointRequesterUnauthorisedException):
        await method_to_test(TEST_URL)
