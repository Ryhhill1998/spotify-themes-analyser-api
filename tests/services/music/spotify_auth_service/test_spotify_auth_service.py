import pytest

from api.services.endpoint_requester import EndpointRequesterException
from api.services.music.spotify_auth_service import SpotifyAuthService, SpotifyAuthServiceException

TEST_URL = "http://test-url.com"
TEST_CLIENT_ID = "client_id"
TEST_CLIENT_SECRET = "client_secret"
TEST_REDIRECT_URI = "http://redirect-test-url.com"
TEST_SCOPE = "user-top-read"

# 1. Test that auth_header generates the authorisation header correctly.
# 2. Test that generate_auth_url returns expected url.
# 3. Test that _get_tokens raises SpotifyAuthServiceException if Spotify API request fails.
# 4. Test that _get_tokens raises SpotifyAuthServiceException if access_token not returned by Spotify.
# 5. Test that create_tokens returns expected TokenData.
# 6. Test that refresh_tokens updates access_token always.
# 7. Test that refresh_tokens updates refresh_token if new one returned by Spotify.
# 8. Test that refresh_tokens keeps refresh_token if new one not returned by Spotify.

@pytest.fixture
def spotify_auth_service(mock_endpoint_requester) -> SpotifyAuthService:
    return SpotifyAuthService(
        client_id=TEST_CLIENT_ID,
        client_secret=TEST_CLIENT_SECRET,
        base_url=TEST_URL,
        redirect_uri=TEST_REDIRECT_URI,
        auth_scope=TEST_SCOPE,
        endpoint_requester=mock_endpoint_requester
    )


@pytest.fixture
def mock_request_tokens_response() -> dict[str, str]:
    return {"access_token": "new_access", "refresh_token": "new_refresh"}


def test_auth_header(spotify_auth_service):
    auth_header = spotify_auth_service._auth_header
    expected_auth_header = "Y2xpZW50X2lkOmNsaWVudF9zZWNyZXQ="

    assert auth_header == expected_auth_header


def test_generate_auth_url(spotify_auth_service):
    state = "state"
    auth_url = spotify_auth_service.generate_auth_url(state)
    expected_auth_url = (
        f"{TEST_URL}/authorize?client_id={TEST_CLIENT_ID}&response_type=code&"
        f"redirect_uri={TEST_REDIRECT_URI.replace('://', '%3A%2F%2F')}&scope={TEST_SCOPE}&state={state}"
    )

    assert auth_url == expected_auth_url


@pytest.mark.asyncio
async def test__get_tokens_request_failure(spotify_auth_service, mock_endpoint_requester):
    mock_endpoint_requester.post.side_effect = EndpointRequesterException()

    with pytest.raises(SpotifyAuthServiceException, match="Spotify API token request failed"):
        await spotify_auth_service._get_tokens(data={}, refresh_token="refresh")


@pytest.mark.asyncio
async def test__get_tokens_invalid_response_data(spotify_auth_service, mock_endpoint_requester):
    mock_endpoint_requester.post.return_value = {}

    with pytest.raises(SpotifyAuthServiceException, match="Failed to validate tokens"):
        await spotify_auth_service._get_tokens(data={}, refresh_token="refresh")


@pytest.mark.asyncio
async def test_create_tokens_no_refresh_token(spotify_auth_service, mock_endpoint_requester, mock_request_tokens_response):
    mock_endpoint_requester.post.return_value = mock_request_tokens_response
    mock_request_tokens_response.pop("refresh_token")

    with pytest.raises(SpotifyAuthServiceException, match="Failed to validate tokens"):
        await spotify_auth_service.create_tokens("auth_code")


@pytest.mark.asyncio
async def test_create_tokens_success(spotify_auth_service, mock_endpoint_requester, mock_request_tokens_response):
    mock_endpoint_requester.post.return_value = mock_request_tokens_response

    tokens = await spotify_auth_service.create_tokens("auth_code")

    assert tokens.access_token == "new_access" and tokens.refresh_token == "new_refresh"


@pytest.mark.asyncio
async def test_refresh_tokens_new_refresh_token_returned(
        spotify_auth_service,
        mock_endpoint_requester,
        mock_request_tokens_response
):
    mock_endpoint_requester.post.return_value = mock_request_tokens_response

    tokens = await spotify_auth_service.refresh_tokens("old_refresh")

    assert tokens.access_token == "new_access" and tokens.refresh_token == "new_refresh"


@pytest.mark.asyncio
async def test_refresh_tokens_no_new_refresh_token_returned(
        spotify_auth_service,
        mock_endpoint_requester,
        mock_request_tokens_response
):
    old_refresh_token = "old_refresh"
    mock_endpoint_requester.post.return_value = mock_request_tokens_response
    mock_request_tokens_response.pop("refresh_token")

    tokens = await spotify_auth_service.refresh_tokens(old_refresh_token)

    assert (
            tokens.access_token == "new_access" and
            tokens.refresh_token != "new_refresh" and
            tokens.refresh_token == old_refresh_token
    )
