from enum import Enum
import urllib.parse

import pydantic

from api.models import TopItemsResponse, TopItem, TopTrack, TopArtist, TokenData, TrackArtist, TopItemResponse
from api.services.endpoint_requester import EndpointRequester, EndpointRequesterUnauthorisedException, \
    EndpointRequesterNotFoundException
from api.services.music.music_service import MusicService
from api.services.music.spotify_auth_service import SpotifyAuthService


class SpotifyDataServiceException(Exception):
    """
    Exception raised when the SpotifyDataService fails to process the API response.

    Parameters
    ----------
    message : str
        The error message describing the failure.
    """

    def __init__(self, message):
        super().__init__(message)


class SpotifyDataServiceNotFoundException(SpotifyDataServiceException):
    """
    Exception raised when SpotifyDataService fails to return results for the request.

    Parameters
    ----------
    message : str
        The error message describing the resource that was not found.
    """

    def __init__(self, message):
        super().__init__(message)


class TopItemType(Enum):
    """
    Enum representing the types of top items that can be retrieved from Spotify.
    """

    ARTISTS = "artists"
    TRACKS = "tracks"


class TimeRange(Enum):
    """
    Enum representing the time range options for retrieving top items.
    """

    SHORT = "short_term"
    MEDIUM = "medium_term"
    LONG = "long_term"


class SpotifyDataService(MusicService):
    """
    Service responsible for interacting with Spotify's API to fetch user-related music data.

    This class provides methods to retrieve a user's top tracks and artists, as well as fetching
    specific items by their Spotify ID.

    Inherits from
    -------------
    MusicService, which provides core attributes such as client_id, client_secret, base_url and endpoint_requester.

    Attributes
    ----------
    spotify_auth_service : SpotifyAuthService
        The authentication service used for handling token management.
    """

    def __init__(
            self,
            client_id: str,
            client_secret: str,
            base_url: str,
            endpoint_requester: EndpointRequester,
            spotify_auth_service: SpotifyAuthService
    ):
        """
        Parameters
        ----------
        client_id : str
            The Spotify API client ID.
        client_secret : str
            The Spotify API client secret.
        base_url : str
            The base URL of the Spotify Web API.
        endpoint_requester : EndpointRequester
            The service responsible for making API requests.
        spotify_auth_service : SpotifyAuthService
            The authentication service used for handling token management.
        """

        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            base_url=base_url,
            endpoint_requester=endpoint_requester
        )
        self.spotify_auth_service = spotify_auth_service

    @staticmethod
    def _create_top_track_object(data: dict) -> TopTrack:
        """
        Creates a TopTrack object from Spotify API data.

        Parameters
        ----------
        data : dict
            The track data received from Spotify's API.

        Returns
        -------
        TopTrack
            A validated TopTrack object.

        Raises
        -------
        KeyError
            If a required key is not present within data.
        """

        album = data["album"]
        artist = data["artists"][0]

        track_artist = TrackArtist(id=artist["id"], name=artist["name"])

        top_track = TopTrack(
            id=data["id"],
            name=data["name"],
            images=album["images"],
            spotify_url=data["external_urls"]["spotify"],
            artist=track_artist,
            release_date=album["release_date"],
            explicit=data["explicit"],
            duration_ms=data["duration_ms"],
            popularity=data["popularity"]
        )

        return top_track

    @staticmethod
    def _create_top_artist_object(data: dict) -> TopArtist:
        """
        Creates a TopArtist object from Spotify API data.

        Parameters
        ----------
        data : dict
            The artist data received from Spotify's API.

        Returns
        -------
        TopArtist
            A validated TopArtist object.

        Raises
        -------
        KeyError
            If a required key is not present within data.
        """

        top_artist = TopArtist(
            id=data["id"],
            name=data["name"],
            images=data["images"],
            spotify_url=data["external_urls"]["music"],
            genres=data["genres"]
        )

        return top_artist

    def _create_top_item_object(self, data: dict, item_type: TopItemType) -> TopItem:
        """
        Creates a TopItem object based on the specified item type.

        Parameters
        ----------
        data : dict
            The item data received from Spotify's API.
        item_type : TopItemType
            The type of item to create (TRACKS or ARTISTS).

        Returns
        -------
        TopItem
            A validated TopItem object.

        Raises
        ------
        SpotifyDataServiceException
            If a required field is missing or if the item type is invalid.
        """

        try:
            if item_type == TopItemType.TRACKS:
                return self._create_top_track_object(data=data)
            elif item_type == TopItemType.ARTISTS:
                return self._create_top_artist_object(data=data)
            else:
                raise SpotifyDataServiceException(f"Invalid item type - {item_type}")
        except KeyError as e:
            missing_key = e.args[0]
            raise SpotifyDataServiceException(
                f"Missing expected key '{missing_key}' in response data for {item_type.value}"
            )
        except pydantic.ValidationError as e:
            print(f"Failed to create TopItem from Spotify API data: {e}")
            raise SpotifyDataServiceException(
                f"Failed to create TopItem from Spotify API data - data: {data}, type: {item_type}"
            )

    async def _get_top_items(
            self,
            access_token: str,
            item_type: TopItemType,
            time_range: str,
            limit: int
    ) -> list[TopItem]:
        """
        Fetches a user's top items from Spotify.

        Parameters
        ----------
        access_token : str
            The user's Spotify access token.
        item_type : TopItemType
            The type of items to retrieve (TRACKS or ARTISTS).
        time_range : str
            The time range for retrieving top items.
        limit : int
            The number of top items to retrieve.

        Returns
        -------
        list[TopItem]
            A list of the user's top items.

        Raises
        -------
        EndpointRequesterUnauthorisedException
            If the request to the Spotify API fails due to a 401 Unauthorised status code.
        EndpointRequesterNotFoundException
            If the request to the Spotify API fails due to a 404 Not Found status code.
        EndpointRequesterException
            If there is an error while making the request to the Spotify API.
        SpotifyDataServiceException
            If the API response data is missing expected fields or fails validation.
        """

        params = {"time_range": time_range, "limit": limit}
        url = f"{self.base_url}/me/top/{item_type.value}?" + urllib.parse.urlencode(params)

        data = await self.endpoint_requester.get(url=url, headers={"Authorization": f"Bearer {access_token}"})

        top_items = [self._create_top_item_object(data=entry, item_type=item_type) for entry in data["items"]]

        return top_items

    async def get_top_items(
            self,
            tokens: TokenData,
            item_type: TopItemType,
            time_range: TimeRange = TimeRange.MEDIUM,
            limit: int = 20
    ) -> TopItemsResponse:
        """
        Retrieves the top items (tracks or artists) for a user.

        Parameters
        ----------
        tokens : TokenData
            The user's access and refresh tokens.
        item_type : TopItemType
            The type of items to retrieve (TRACKS or ARTISTS).
        time_range : TimeRange, optional
            The time range for retrieving top items, default is MEDIUM.
        limit : int, optional
            The number of top items to retrieve, default is 20.

        Returns
        -------
        TopItemsResponse
            A response containing the user's top items and updated tokens.

        Raises
        ------
        EndpointRequesterUnauthorisedException
            If the request to the Spotify API fails due to a 401 Unauthorised status code.
        EndpointRequesterException
            If there is an error while making the request to the Spotify API.
        SpotifyDataServiceNotFoundException
            If no top items are found.
        SpotifyDataServiceException
            If the API response data is missing expected fields or fails validation.
        """

        try:
            top_items = await self._get_top_items(
                access_token=tokens.access_token,
                item_type=item_type,
                time_range=time_range.value,
                limit=limit
            )
        except EndpointRequesterUnauthorisedException:
            tokens = await self.spotify_auth_service.refresh_tokens(refresh_token=tokens.refresh_token)
            top_items = await self._get_top_items(
                access_token=tokens.access_token,
                item_type=item_type,
                time_range=time_range.value,
                limit=limit
            )

        if len(top_items) == 0:
            raise SpotifyDataServiceNotFoundException(f"No top items found - type: {item_type}")

        top_items_response = TopItemsResponse(data=top_items, tokens=tokens)

        return top_items_response

    async def _get_item_by_id(self, item_id: str, tokens: TokenData, item_type: TopItemType) -> TopItem:
        """
        Fetches a specific item (track or artist) from the Spotify API using its unique identifier.

        Parameters
        ----------
        item_id : str
            The unique identifier of the item (track or artist) to retrieve.
        tokens : TokenData
            The user's authentication tokens required for making the API request.
        item_type : TopItemType
            The type of the item being requested (e.g., TRACKS or ARTISTS).

        Returns
        -------
        TopItem
            An object representing the retrieved track or artist.

        Raises
        ------
        EndpointRequesterUnauthorisedException
            If the request to the Spotify API fails due to a 401 Unauthorised status code.
        EndpointRequesterNotFoundException
            If the request to the Spotify API fails due to a 404 Not Found status code.
        EndpointRequesterException
            If there is an error while making the request to the Spotify API.
        SpotifyDataServiceException
            If the response data is missing expected fields or fails validation.
        """

        url = f"{self.base_url}/{item_type.value}/{item_id}"

        data = await self.endpoint_requester.get(url=url, headers={"Authorization": f"Bearer {tokens.access_token}"})

        item = self._create_top_item_object(data=data, item_type=item_type)

        return item

    async def get_item_by_id(self, item_id: str, tokens: TokenData, item_type: TopItemType) -> TopItemResponse:
        """
        Retrieves a specific track or artist by its unique identifier, handling authentication and errors.

        If the request fails due to an expired or invalid token, it attempts to refresh the token and retry.

        Parameters
        ----------
        item_id : str
            The unique identifier of the item (track or artist) to retrieve.
        tokens : TokenData
            The user's authentication tokens required for making the API request.
        item_type : TopItemType
            The type of the item being requested (e.g., TRACKS or ARTISTS).

        Returns
        -------
        TopItemResponse
            A response object containing the retrieved item along with updated authentication tokens.

        Raises
        ------
        EndpointRequesterUnauthorisedException
            If the request to the Spotify API fails twice due to a 401 Unauthorised status code.
        EndpointRequesterException
            If there is an error while making the request to the Spotify API.
        SpotifyDataServiceNotFoundException
            If the requested item does not exist.
        SpotifyDataServiceException
            If the response data is missing expected fields or fails validation.
        """

        try:
            item = await self._get_item_by_id(item_id=item_id, tokens=tokens, item_type=item_type)
        except EndpointRequesterUnauthorisedException:
            tokens = await self.spotify_auth_service.refresh_tokens(refresh_token=tokens.refresh_token)
            item = await self._get_item_by_id(item_id=item_id, tokens=tokens, item_type=item_type)
        except EndpointRequesterNotFoundException:
            raise SpotifyDataServiceNotFoundException(f"Requested item not found - ID: {item_id}, type: {item_type}")

        item_response = TopItemResponse(data=item, tokens=tokens)

        return item_response
