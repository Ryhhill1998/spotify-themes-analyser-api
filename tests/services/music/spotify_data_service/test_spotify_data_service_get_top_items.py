import pytest

from api.models import SpotifyTrack, SpotifyTrackArtist, SpotifyItemsResponse, SpotifyItemImage, SpotifyArtist
from api.services.endpoint_requester import EndpointRequesterException, EndpointRequesterUnauthorisedException
from api.services.music.spotify_auth_service import SpotifyAuthServiceException
from api.services.music.spotify_data_service import SpotifyDataServiceException, ItemType

TEST_URL = "http://test-url.com"

# 1. Test get_top_items raises SpotifyDataServiceException if API data request fails.
# 2. Test get_top_items tries to refresh tokens if API request raises unauthorised error.
# 3. Test get_top_items raises SpotifyDataServiceException if token refresh fails.
# 4. Test get_top_items raises SpotifyDataServiceException if data validation fails.
# 5. Test get_top_items returns expected response.


@pytest.fixture
def mock_track_data_factory():
    def _create(track_id: str, track_name: str, artist_id: str, artist_name: str):
        return {
            "id": track_id,
            "name": track_name,
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
                    "id": artist_id,
                    "name": artist_name
                }
            ],
            "explicit": False,
            "duration_ms": 100,
            "popularity": 50
        }

    return _create


@pytest.fixture
def mock_tracks(mock_track_data_factory) -> dict:
    return {
        "items": [
            mock_track_data_factory(
                track_id=str(i),
                track_name=f"Track {i}",
                artist_id=str(i),
                artist_name=f"Artist {i}"
            )
            for i
            in range(2)
        ]
    }


@pytest.fixture
def mock_artist_data_factory():
    def _create(artist_id: str, artist_name: str):
        return {
            "id": artist_id,
            "name": artist_name,
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

    return _create


@pytest.fixture
def mock_artists(mock_artist_data_factory) -> dict:
    return {
        "items": [
            mock_artist_data_factory(
                artist_id=str(i),
                artist_name=f"Artist {i}"
            ) for i
            in range(2)
        ]
    }


# -------------------- GET TOP ITEMS -------------------- #

# GENERIC
@pytest.mark.asyncio
async def test_get_top_items_request_failure(spotify_data_service, mock_endpoint_requester, mock_request_tokens):
    mock_endpoint_requester.get.side_effect = EndpointRequesterException()

    with pytest.raises(SpotifyDataServiceException, match="Request to Spotify API failed"):
        await spotify_data_service.get_top_items(tokens=mock_request_tokens, item_type=ItemType.TRACKS)


@pytest.mark.asyncio
async def test_get_top_items_unauthorised_request(
        spotify_data_service,
        mock_endpoint_requester,
        mock_spotify_auth_service,
        mock_request_tokens
):
    mock_endpoint_requester.get.side_effect = EndpointRequesterUnauthorisedException()
    mock_spotify_auth_service.refresh_tokens.return_value = mock_request_tokens

    with pytest.raises(SpotifyDataServiceException, match="Request to Spotify API failed"):
        await spotify_data_service.get_top_items(tokens=mock_request_tokens, item_type=ItemType.TRACKS)

    mock_spotify_auth_service.refresh_tokens.assert_called_once_with(mock_request_tokens.refresh_token)
    assert mock_endpoint_requester.get.call_count == 2


@pytest.mark.parametrize("item_type", [ItemType.TRACKS, ItemType.ARTISTS])
@pytest.mark.asyncio
async def test_get_top_items_token_refresh_failure(
        spotify_data_service,
        mock_endpoint_requester,
        mock_spotify_auth_service,
        mock_request_tokens,
        item_type
):
    mock_endpoint_requester.get.side_effect = EndpointRequesterUnauthorisedException()
    mock_spotify_auth_service.refresh_tokens.side_effect = SpotifyAuthServiceException("Test")

    with pytest.raises(SpotifyDataServiceException, match="Failed to refresh access token"):
        await spotify_data_service.get_top_items(tokens=mock_request_tokens, item_type=item_type)

    mock_spotify_auth_service.refresh_tokens.assert_called_once_with(mock_request_tokens.refresh_token)
    mock_endpoint_requester.get.assert_called_once_with(
        url=f"{TEST_URL}/me/top/{item_type.value}?time_range=medium_term&limit=10",
        headers={"Authorization": f"Bearer {mock_request_tokens.access_token}"}
    )


@pytest.mark.parametrize("item_type", [ItemType.TRACKS, ItemType.ARTISTS])
@pytest.mark.asyncio
async def test_invalid_api_response_type(spotify_data_service, mock_endpoint_requester, mock_request_tokens, item_type):
    mock_endpoint_requester.get.return_value = {"items": "invalid"}

    with pytest.raises(SpotifyDataServiceException, match="Spotify data not of type dict. Actual type: <class 'str'>"):
        await spotify_data_service.get_top_items(tokens=mock_request_tokens, item_type=item_type)


# TRACKS
@pytest.mark.parametrize(
    "missing_attr",
    ["id", "name", "external_urls", "album", "artists", "explicit", "duration_ms", "popularity"]
)
@pytest.mark.asyncio
async def test_get_top_items_tracks_response_data_missing_fields(
        spotify_data_service,
        mock_endpoint_requester,
        mock_request_tokens,
        mock_tracks,
        missing_attr
):
    mock_endpoint_requester.get.return_value = mock_tracks
    mock_tracks["items"][0].pop(missing_attr)

    with pytest.raises(SpotifyDataServiceException, match="Failed to create TopItem from Spotify API data"):
        await spotify_data_service.get_top_items(tokens=mock_request_tokens, item_type=ItemType.TRACKS)


@pytest.mark.parametrize("none_type_attr", ["id", "name", "explicit", "duration_ms", "popularity"])
@pytest.mark.asyncio
async def test_get_top_items_tracks_response_data_none_type_fields(
        spotify_data_service,
        mock_endpoint_requester,
        mock_request_tokens,
        mock_tracks,
        none_type_attr
):
    mock_endpoint_requester.get.return_value = mock_tracks
    mock_tracks["items"][0][none_type_attr] = None

    with pytest.raises(SpotifyDataServiceException, match="Failed to create TopItem from Spotify API data"):
        await spotify_data_service.get_top_items(tokens=mock_request_tokens, item_type=ItemType.TRACKS)


@pytest.mark.parametrize("invalid_attr", ["external_urls", "album", "artists"])
@pytest.mark.asyncio
async def test_get_top_items_tracks_response_data_invalid_field_types(
        spotify_data_service,
        mock_endpoint_requester,
        mock_request_tokens,
        mock_tracks,
        invalid_attr
):
    mock_endpoint_requester.get.return_value = mock_tracks
    mock_tracks["items"][0][invalid_attr] = "invalid"

    with pytest.raises(SpotifyDataServiceException, match="Failed to create TopItem from Spotify API data"):
        await spotify_data_service.get_top_items(tokens=mock_request_tokens, item_type=ItemType.TRACKS)


@pytest.mark.asyncio
async def test_get_top_items_tracks_success(spotify_data_service, mock_endpoint_requester, mock_request_tokens, mock_tracks):
    mock_endpoint_requester.get.return_value = mock_tracks
    expected_tracks = [
        SpotifyTrack(
            id="0",
            name=f"Track 0",
            images=[
                SpotifyItemImage(height=640, width=640, url="http://image-url.com")
            ],
            spotify_url="http://spotify-test-url.com",
            artist=SpotifyTrackArtist(id="0", name=f"Artist 0"),
            release_date="01/01/1999",
            explicit=False,
            duration_ms=100,
            popularity=50
        ),
        SpotifyTrack(
            id="1",
            name=f"Track 1",
            images=[
                SpotifyItemImage(height=640, width=640, url="http://image-url.com")
            ],
            spotify_url="http://spotify-test-url.com",
            artist=SpotifyTrackArtist(id="1", name=f"Artist 1"),
            release_date="01/01/1999",
            explicit=False,
            duration_ms=100,
            popularity=50
        )
    ]
    expected_response = SpotifyItemsResponse(data=expected_tracks, tokens=mock_request_tokens)

    response = await spotify_data_service.get_top_items(tokens=mock_request_tokens, item_type=ItemType.TRACKS)

    assert response == expected_response


# ARTISTS
@pytest.mark.parametrize("missing_attr", ["id", "name", "images", "external_urls", "genres"])
@pytest.mark.asyncio
async def test_get_top_items_artists_response_data_missing_fields(
        spotify_data_service,
        mock_endpoint_requester,
        mock_request_tokens,
        mock_artists,
        missing_attr
):
    mock_endpoint_requester.get.return_value = mock_artists
    mock_artists["items"][0].pop(missing_attr)

    with pytest.raises(SpotifyDataServiceException, match="Failed to create TopItem from Spotify API data"):
        await spotify_data_service.get_top_items(tokens=mock_request_tokens, item_type=ItemType.ARTISTS)


@pytest.mark.parametrize("none_type_attr", ["id", "name"])
@pytest.mark.asyncio
async def test_get_top_items_artists_response_data_none_type_fields(
        spotify_data_service,
        mock_endpoint_requester,
        mock_request_tokens,
        mock_artists,
        none_type_attr
):
    mock_endpoint_requester.get.return_value = mock_artists
    mock_artists["items"][0][none_type_attr] = None

    with pytest.raises(SpotifyDataServiceException, match="Failed to create TopItem from Spotify API data"):
        await spotify_data_service.get_top_items(tokens=mock_request_tokens, item_type=ItemType.ARTISTS)


@pytest.mark.parametrize("invalid_attr", ["images", "external_urls"])
@pytest.mark.asyncio
async def test_get_top_items_artists_response_data_invalid_field_types(
        spotify_data_service,
        mock_endpoint_requester,
        mock_request_tokens,
        mock_artists,
        invalid_attr
):
    mock_endpoint_requester.get.return_value = mock_artists
    mock_artists["items"][0][invalid_attr] = None

    with pytest.raises(SpotifyDataServiceException, match="Failed to create TopItem from Spotify API data"):
        await spotify_data_service.get_top_items(tokens=mock_request_tokens, item_type=ItemType.ARTISTS)


@pytest.mark.asyncio
async def test_get_top_items_artists_success(spotify_data_service, mock_endpoint_requester, mock_request_tokens, mock_artists):
    mock_endpoint_requester.get.return_value = mock_artists
    expected_artists = [
        SpotifyArtist(
            id="0",
            name=f"Artist 0",
            images=[
                SpotifyItemImage(height=640, width=640, url="http://image-url.com")
            ],
            spotify_url="http://spotify-test-url.com",
            genres=["genre1", "genre2"]
        ),
        SpotifyArtist(
            id="1",
            name=f"Artist 1",
            images=[
                SpotifyItemImage(height=640, width=640, url="http://image-url.com")
            ],
            spotify_url="http://spotify-test-url.com",
            genres=["genre1", "genre2"]
        ),
    ]
    expected_response = SpotifyItemsResponse(data=expected_artists, tokens=mock_request_tokens)

    response = await spotify_data_service.get_top_items(tokens=mock_request_tokens, item_type=ItemType.ARTISTS)

    assert response == expected_response
