from unittest.mock import Mock
from fastapi import Request
from fastapi.exceptions import HTTPException

import pytest

from api.dependencies import get_tokens_from_cookies


@pytest.fixture
def mock_request() -> Mock:
    return Mock(spec=Request)


@pytest.fixture
def mock_cookies() -> dict:
    return {"access_token": "access", "refresh_token": "refresh"}


@pytest.mark.parametrize("cookies_to_remove", [["access_token"], ["refresh_token"], ["access_token", "refresh_token"]])
def test_get_tokens_from_cookies_unauthorised_request(mock_request, mock_cookies, cookies_to_remove):
    for cookie in cookies_to_remove:
        mock_cookies.pop(cookie)
    mock_request.cookies = mock_cookies

    with pytest.raises(HTTPException, match="Requests must include an access token and a refresh token.") as e:
        get_tokens_from_cookies(mock_request)

    assert e.value.status_code == 401


def test_get_tokens_from_cookies_success(mock_request, mock_cookies):
    mock_request.cookies = mock_cookies

    tokens = get_tokens_from_cookies(mock_request)

    assert tokens.access_token == mock_cookies["access_token"] and tokens.refresh_token == mock_cookies["refresh_token"]
