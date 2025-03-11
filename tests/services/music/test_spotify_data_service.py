from unittest.mock import AsyncMock

import pytest

from api.services.endpoint_requester import EndpointRequester, EndpointRequesterException
from api.services.music.spotify_auth_service import SpotifyAuthService
from api.services.music.spotify_data_service import SpotifyDataService, SpotifyDataServiceException

TEST_URL = "http://test-url.com"
TEST_CLIENT_ID = "client_id"
TEST_CLIENT_SECRET = "client_secret"
TEST_REDIRECT_URI = "http://redirect-test-url.com"
TEST_SCOPE = "user-top-read"


# 1. Test get_top_items raises SpotifyDataServiceException if API data request fails.
# 2. Test get_top_items tries to refresh tokens if API request raises unauthorised error.
# 3. Test get_top_items raises SpotifyDataServiceException if token refresh fails.
# 4. Test get_top_items raises SpotifyDataServiceException if data validation fails.
# 5. Test get_top_items returns expected response.
# 6. Test get_item_by_id raises SpotifyDataServiceException if Spotify API request fails.
# 7. Test get_item_by_id raises SpotifyDataServiceNotFoundException if item not found on Spotify.
# 8. Test get_item_by_id tries to refresh tokens if API request raises unauthorised error.
# 9. Test get_item_by_id raises SpotifyDataServiceException if token refresh fails.
# 10. Test get_item_by_id raises SpotifyDataServiceException if data validation fails.
# 11. Test get_item_by_id returns expected response.


@pytest.fixture
def mock_endpoint_requester() -> AsyncMock:
    return AsyncMock(spec=EndpointRequester)


@pytest.fixture
def mock_spotify_auth_service() -> AsyncMock:
    return AsyncMock(spec=SpotifyAuthService)


@pytest.fixture
def spotify_data_service(mock_endpoint_requester, mock_spotify_auth_service) -> SpotifyDataService:
    return SpotifyDataService(
        client_id=TEST_CLIENT_ID,
        client_secret=TEST_CLIENT_SECRET,
        base_url=TEST_URL,
        endpoint_requester=mock_endpoint_requester,
        spotify_auth_service=mock_spotify_auth_service
    )


@pytest.mark.asyncio
async def test_get_top_items_request_failure(spotify_data_service):
    pass


@pytest.mark.asyncio
async def test_get_top_items_unauthorised_request(spotify_data_service):
    pass


@pytest.mark.asyncio
async def test_get_top_items_token_refresh_failure(spotify_data_service):
    pass


@pytest.mark.asyncio
async def test_get_top_items_invalid_response_data(spotify_data_service):
    pass


@pytest.mark.asyncio
async def test_get_top_items_success(spotify_data_service):
    pass


@pytest.mark.asyncio
async def test_get_item_by_id_request_failure(spotify_data_service):
    pass


@pytest.mark.asyncio
async def test_get_item_by_id_item_not_found(spotify_data_service):
    pass


@pytest.mark.asyncio
async def test_get_item_by_id_unauthorised_request(spotify_data_service):
    pass


@pytest.mark.asyncio
async def test_get_item_by_id_token_refresh_failure(spotify_data_service):
    pass


@pytest.mark.asyncio
async def test_get_item_by_id_invalid_response_data(spotify_data_service):
    pass


@pytest.mark.asyncio
async def test_get_item_by_id_success(spotify_data_service):
    pass
