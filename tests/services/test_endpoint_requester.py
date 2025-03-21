import json
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from api.services.endpoint_requester import EndpointRequester, EndpointRequesterException, \
    EndpointRequesterUnauthorisedException, EndpointRequesterNotFoundException

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
async def test_http_status_error(endpoint_requester, mock_httpx_client, mock_response_failure, method):
    """Test that HTTP status errors (except 401) raise EndpointRequesterException."""
    mock_response_failure.status_code = 500
    mock_httpx_client.request.return_value = mock_response_failure
    method_to_test = getattr(endpoint_requester, method)

    with pytest.raises(EndpointRequesterException, match="Request failed"):
        await method_to_test(TEST_URL)


@pytest.mark.parametrize("method", ["get", "post"])
@pytest.mark.asyncio
async def test_unauthorised_error(endpoint_requester, mock_httpx_client, mock_response_failure, method):
    """Test that a 401 response raises EndpointRequesterUnauthorisedException."""
    mock_response_failure.status_code = 401
    mock_httpx_client.request.return_value = mock_response_failure
    method_to_test = getattr(endpoint_requester, method)

    with pytest.raises(EndpointRequesterUnauthorisedException, match="Unauthorised request"):
        await method_to_test(TEST_URL)


@pytest.mark.parametrize("method", ["get", "post"])
@pytest.mark.asyncio
async def test_not_found_error(endpoint_requester, mock_httpx_client, mock_response_failure, method):
    """Test that a 404 response raises EndpointRequesterNotFoundException."""
    mock_response_failure.status_code = 404
    mock_httpx_client.request.return_value = mock_response_failure
    method_to_test = getattr(endpoint_requester, method)

    with pytest.raises(EndpointRequesterNotFoundException, match="Resource not found"):
        await method_to_test(TEST_URL)


@pytest.mark.parametrize("method", ["get", "post"])
@pytest.mark.asyncio
async def test_json_decode_error(endpoint_requester, mock_httpx_client, mock_response_success, method):
    """Test that invalid JSON in the response raises EndpointRequesterException."""
    mock_httpx_client.request.return_value = mock_response_success
    mock_response_success.raise_for_status.return_value = None
    mock_response_success.json.side_effect = json.JSONDecodeError("Expecting value", "doc", 0)
    mock_httpx_client.request.return_value = mock_response_success

    method_to_test = getattr(endpoint_requester, method)

    with pytest.raises(EndpointRequesterException, match="Invalid JSON response"):
        await method_to_test(TEST_URL)


@pytest.mark.parametrize("method", ["get", "post"])
@pytest.mark.asyncio
async def test_timeout_error(endpoint_requester, mock_httpx_client, method):
    """Test that a request timeout raises EndpointRequesterException."""
    mock_httpx_client.request.side_effect = httpx.TimeoutException("Request timeout")

    method_to_test = getattr(endpoint_requester, method)

    with pytest.raises(EndpointRequesterException, match="Request timeout"):
        await method_to_test(TEST_URL)


@pytest.mark.parametrize("method", ["get", "post"])
@pytest.mark.asyncio
async def test_request_error(endpoint_requester, mock_httpx_client, method):
    """Test that a generic request error raises EndpointRequesterException."""
    mock_httpx_client.request.side_effect = httpx.RequestError("Request failed")

    method_to_test = getattr(endpoint_requester, method)

    with pytest.raises(EndpointRequesterException, match="Request failed"):
        await method_to_test(TEST_URL)


@pytest.mark.parametrize("method", ["get", "post"])
@pytest.mark.asyncio
async def test_invalid_url_error(endpoint_requester, mock_httpx_client, method):
    """Test that an invalid URL raises EndpointRequesterException."""
    mock_httpx_client.request.side_effect = httpx.InvalidURL("Invalid URL")

    method_to_test = getattr(endpoint_requester, method)

    with pytest.raises(EndpointRequesterException, match="Invalid URL"):
        await method_to_test(TEST_URL)
