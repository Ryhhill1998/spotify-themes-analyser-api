from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from api.services.endpoint_requester import EndpointRequester


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


@pytest.mark.asyncio
async def test_get_success(endpoint_requester, mock_httpx_client, mock_response_success):
    """Test GET request with 2XX status code response returns expected data"""
    mock_httpx_client.get.return_value = mock_response_success
    url = "http://test-url.com"

    data = await endpoint_requester.get(url)

    assert data == SUCCESS_RESPONSE
    mock_httpx_client.get.assert_called_once_with(url=url, headers=None, params=None, timeout=None)


@pytest.mark.asyncio
async def test_get_failure(endpoint_requester, mock_httpx_client, mock_response_failure):
    """Test GET request with non-2XX status code response raises HTTPStatusError"""
    mock_httpx_client.get.return_value = mock_response_failure
    url = "http://test-url.com"

    with pytest.raises(httpx.HTTPStatusError) as e:
        await endpoint_requester.get(url)

    assert str(e.value) == ERROR_RESPONSE


@pytest.mark.asyncio
async def test_post_success(endpoint_requester, mock_httpx_client, mock_response_success):
    """Test POST request with 2XX status code response returns expected data"""
    mock_httpx_client.post.return_value = mock_response_success
    url = "http://test-url.com"

    data = await endpoint_requester.post(url)

    assert data == SUCCESS_RESPONSE
    mock_httpx_client.post.assert_called_once_with(url=url, headers=None, data=None, json=None, timeout=None)


@pytest.mark.asyncio
async def test_post_failure(endpoint_requester, mock_httpx_client, mock_response_failure):
    """Test POST request with non-2XX status code response raises HTTPStatusError"""
    mock_httpx_client.post.return_value = mock_response_failure
    url = "http://test-url.com"

    with pytest.raises(httpx.HTTPStatusError) as e:
        await endpoint_requester.post(url)

    assert str(e.value) == ERROR_RESPONSE
