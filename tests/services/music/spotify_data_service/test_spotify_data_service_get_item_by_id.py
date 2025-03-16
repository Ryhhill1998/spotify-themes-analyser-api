import pytest

from api.models import SpotifyTrack, SpotifyTrackArtist, SpotifyItemImage, SpotifyArtist, SpotifyItemResponse
from api.services.endpoint_requester import EndpointRequesterException, EndpointRequesterUnauthorisedException, \
    EndpointRequesterNotFoundException
from api.services.music.spotify_auth_service import SpotifyAuthServiceException
from api.services.music.spotify_data_service import SpotifyDataServiceException, ItemType, \
    SpotifyDataServiceNotFoundException

TEST_URL = "http://test-url.com"

# 1. Test get_item_by_id raises SpotifyDataServiceException if Spotify API request fails.
# 2. Test get_item_by_id raises SpotifyDataServiceNotFoundException if item not found on Spotify.
# 3. Test get_item_by_id tries to refresh tokens if API request raises unauthorised error.
# 4. Test get_item_by_id raises SpotifyDataServiceException if token refresh fails.
# 5. Test get_item_by_id raises SpotifyDataServiceException if data validation fails.
# 6. Test get_item_by_id returns expected response.


@pytest.fixture
def mock_track_data() -> dict:
    return {
        "id": "1",
        "name": "Track 0",
        "external_urls": {
            "spotify": "http://spotify-test-url.com"
        },
        "album": {
            "images": [
                {
                    "height": 640,
                    "width": 640,
                    "url": "http://image-url.com"
                }
            ],
            "release_date": "01/01/1999"
        },
        "artists": [
            {
                "id": "1",
                "name": "Artist 1"
            }
        ],
        "explicit": False,
        "duration_ms": 100,
        "popularity": 50
    }


@pytest.fixture
def mock_artist_data():
    return {
        "id": "1",
        "name": "Artist 1",
        "images": [
            {
                "height": 640,
                "width": 640,
                "url": "http://image-url.com"
            }
        ],
        "external_urls": {
            "spotify": "http://spotify-test-url.com"
        },
        "genres": ["genre1", "genre2"]
    }


# -------------------- GET ITEM BY ID -------------------- #

# GENERIC
@pytest.mark.asyncio
async def test_get_item_by_id_request_failure(spotify_data_service, mock_endpoint_requester, mock_request_tokens):
    mock_endpoint_requester.get.side_effect = EndpointRequesterException()

    with pytest.raises(SpotifyDataServiceException, match="Request to Spotify API failed"):
        await spotify_data_service.get_item_by_id(item_id="1", tokens=mock_request_tokens, item_type=ItemType.TRACKS)


@pytest.mark.parametrize("item_type", [ItemType.TRACKS, ItemType.ARTISTS])
@pytest.mark.asyncio
async def test_get_item_by_id_item_not_found(
        spotify_data_service,
        mock_endpoint_requester,
        mock_request_tokens,
        item_type
):
    mock_endpoint_requester.get.side_effect = EndpointRequesterNotFoundException()

    with pytest.raises(SpotifyDataServiceNotFoundException, match="Requested item not found"):
        await spotify_data_service.get_item_by_id(item_id="1", tokens=mock_request_tokens, item_type=item_type)


@pytest.mark.asyncio
async def test_get_item_by_id_unauthorised_request(
        spotify_data_service,
        mock_endpoint_requester,
        mock_spotify_auth_service,
        mock_request_tokens
):
    mock_endpoint_requester.get.side_effect = EndpointRequesterUnauthorisedException()
    mock_spotify_auth_service.refresh_tokens.return_value = mock_request_tokens

    with pytest.raises(SpotifyDataServiceException, match="Request to Spotify API failed"):
        await spotify_data_service.get_item_by_id(item_id="1", tokens=mock_request_tokens, item_type=ItemType.TRACKS)

    mock_spotify_auth_service.refresh_tokens.assert_called_once_with(mock_request_tokens.refresh_token)


@pytest.mark.parametrize("item_type", [ItemType.TRACKS, ItemType.ARTISTS])
@pytest.mark.asyncio
async def test_get_item_by_id_token_refresh_failure(
        spotify_data_service,
        mock_endpoint_requester,
        mock_spotify_auth_service,
        mock_request_tokens,
        item_type
):
    mock_endpoint_requester.get.side_effect = EndpointRequesterUnauthorisedException()
    mock_spotify_auth_service.refresh_tokens.side_effect = SpotifyAuthServiceException("Test")
    item_id = "1"

    with pytest.raises(SpotifyDataServiceException, match="Failed to refresh access token"):
        await spotify_data_service.get_item_by_id(item_id=item_id, tokens=mock_request_tokens, item_type=item_type)

    mock_spotify_auth_service.refresh_tokens.assert_called_once_with(mock_request_tokens.refresh_token)
    mock_endpoint_requester.get.assert_called_once_with(
        url=f"{TEST_URL}/{item_type.value}/{item_id}",
        headers={"Authorization": f"Bearer {mock_request_tokens.access_token}"}
    )


@pytest.mark.parametrize("item_type", [ItemType.TRACKS, ItemType.ARTISTS])
@pytest.mark.asyncio
async def test_invalid_api_response_type(spotify_data_service, mock_endpoint_requester, mock_request_tokens, item_type):
    mock_endpoint_requester.get.return_value = "invalid"

    with pytest.raises(SpotifyDataServiceException, match="Spotify data not of type dict. Actual type: <class 'str'>"):
        await spotify_data_service.get_item_by_id(item_id="1", tokens=mock_request_tokens, item_type=item_type)


# TRACKS
@pytest.mark.parametrize(
    "missing_attr",
    ["id", "name", "external_urls", "album", "artists", "explicit", "duration_ms", "popularity"]
)
@pytest.mark.asyncio
async def test_get_item_by_id_track_response_data_missing_fields(
        spotify_data_service,
        mock_endpoint_requester,
        mock_request_tokens,
        mock_track_data,
        missing_attr
):
    mock_endpoint_requester.get.return_value = mock_track_data
    mock_track_data.pop(missing_attr)

    with pytest.raises(SpotifyDataServiceException, match="Failed to create TopItem from Spotify API data"):
        await spotify_data_service.get_item_by_id(item_id="1", tokens=mock_request_tokens, item_type=ItemType.TRACKS)


@pytest.mark.parametrize("none_type_attr", ["id", "name", "explicit", "duration_ms", "popularity"])
@pytest.mark.asyncio
async def test_get_item_by_id_track_response_data_none_type_fields(
        spotify_data_service,
        mock_endpoint_requester,
        mock_request_tokens,
        mock_track_data,
        none_type_attr
):
    mock_endpoint_requester.get.return_value = mock_track_data
    mock_track_data[none_type_attr] = None

    with pytest.raises(SpotifyDataServiceException, match="Failed to create TopItem from Spotify API data"):
        await spotify_data_service.get_item_by_id(item_id="1", tokens=mock_request_tokens, item_type=ItemType.TRACKS)


@pytest.mark.parametrize("invalid_attr", ["external_urls", "album", "artists"])
@pytest.mark.asyncio
async def test_get_item_by_id_track_response_data_invalid_field_types(
        spotify_data_service,
        mock_endpoint_requester,
        mock_request_tokens,
        mock_track_data,
        invalid_attr
):
    mock_endpoint_requester.get.return_value = mock_track_data
    mock_track_data[invalid_attr] = "invalid"

    with pytest.raises(SpotifyDataServiceException, match="Failed to create TopItem from Spotify API data"):
        await spotify_data_service.get_item_by_id(item_id="1", tokens=mock_request_tokens, item_type=ItemType.TRACKS)


@pytest.mark.asyncio
async def test_get_item_by_id_track_success(
        spotify_data_service,
        mock_endpoint_requester,
        mock_request_tokens,
        mock_track_data
):
    mock_endpoint_requester.get.return_value = mock_track_data
    expected_track = SpotifyTrack(
        id="1",
        name=f"Track 0",
        images=[
            SpotifyItemImage(height=640, width=640, url="http://image-url.com")
        ],
        spotify_url="http://spotify-test-url.com",
        artist=SpotifyTrackArtist(id="1", name="Artist 1"),
        release_date="01/01/1999",
        explicit=False,
        duration_ms=100,
        popularity=50
    )
    expected_response = SpotifyItemResponse(data=expected_track, tokens=mock_request_tokens)

    response = await spotify_data_service.get_item_by_id(
        item_id="1",
        tokens=mock_request_tokens,
        item_type=ItemType.TRACKS
    )

    assert response == expected_response


# ARTISTS
@pytest.mark.parametrize("missing_attr", ["id", "name", "images", "external_urls", "genres"])
@pytest.mark.asyncio
async def test_get_item_by_id_artist_response_data_missing_fields(
        spotify_data_service,
        mock_endpoint_requester,
        mock_request_tokens,
        mock_artist_data,
        missing_attr
):
    mock_endpoint_requester.get.return_value = mock_artist_data
    mock_artist_data.pop(missing_attr)

    with pytest.raises(SpotifyDataServiceException, match="Failed to create TopItem from Spotify API data"):
        await spotify_data_service.get_item_by_id(item_id="1", tokens=mock_request_tokens, item_type=ItemType.ARTISTS)


@pytest.mark.parametrize("none_type_attr", ["id", "name"])
@pytest.mark.asyncio
async def test_get_item_by_id_artist_response_data_none_type_fields(
        spotify_data_service,
        mock_endpoint_requester,
        mock_request_tokens,
        mock_artist_data,
        none_type_attr
):
    mock_endpoint_requester.get.return_value = mock_artist_data
    mock_artist_data[none_type_attr] = None

    with pytest.raises(SpotifyDataServiceException, match="Failed to create TopItem from Spotify API data"):
        await spotify_data_service.get_item_by_id(item_id="1", tokens=mock_request_tokens, item_type=ItemType.ARTISTS)


@pytest.mark.parametrize("invalid_attr", ["images", "external_urls"])
@pytest.mark.asyncio
async def test_get_item_by_id_artist_response_data_invalid_field_types(
        spotify_data_service,
        mock_endpoint_requester,
        mock_request_tokens,
        mock_artist_data,
        invalid_attr
):
    mock_endpoint_requester.get.return_value = mock_artist_data
    mock_artist_data[invalid_attr] = None

    with pytest.raises(SpotifyDataServiceException, match="Failed to create TopItem from Spotify API data"):
        await spotify_data_service.get_item_by_id(item_id="1", tokens=mock_request_tokens, item_type=ItemType.ARTISTS)


@pytest.mark.asyncio
async def test_get_item_by_id_artist_success(
        spotify_data_service,
        mock_endpoint_requester,
        mock_request_tokens,
        mock_artist_data
):
    mock_endpoint_requester.get.return_value = mock_artist_data
    expected_artist = SpotifyArtist(
        id="1",
        name=f"Artist 1",
        images=[
            SpotifyItemImage(height=640, width=640, url="http://image-url.com")
        ],
        spotify_url="http://spotify-test-url.com",
        genres=["genre1", "genre2"]
    )
    expected_response = SpotifyItemResponse(data=expected_artist, tokens=mock_request_tokens)

    response = await spotify_data_service.get_item_by_id(
        item_id="1",
        tokens=mock_request_tokens,
        item_type=ItemType.ARTISTS
    )

    assert response == expected_response
