from enum import Enum
import urllib.parse

import pydantic

from api.models import SpotifyItemsResponse, SpotifyItem, SpotifyTrack, SpotifyArtist, TokenData, TrackArtist, SpotifyItemResponse
from api.services.endpoint_requester import EndpointRequester, EndpointRequesterUnauthorisedException, \
    EndpointRequesterNotFoundException, EndpointRequesterException
from api.services.music.music_service import MusicService
from api.services.music.spotify_auth_service import SpotifyAuthService, SpotifyAuthServiceException


class SpotifyDataServiceException(Exception):
    """
    Exception raised when the SpotifyDataService fails to make the API request or process the response data.

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


class ItemType(Enum):
    """
    Enum representing the types of items that can be retrieved from Spotify.

    Attributes
    ----------
    ARTISTS : str
        Represents the artists item type.
    TRACKS : str
        Represents the tracks item type.
    """

    ARTISTS = "artists"
    TRACKS = "tracks"


class TimeRange(Enum):
    """
    Enum representing the time range options for retrieving top items.

    Attributes
    ----------
    SHORT : str
        Represents the short-term time range.
    MEDIUM : str
        Represents the medium-term time range.
    LONG : str
        Represents the long-term time range.
    """

    SHORT = "short_term"
    MEDIUM = "medium_term"
    LONG = "long_term"


class SpotifyDataService(MusicService):
    """
    Service responsible for interacting with Spotify's API to fetch user-related music data.

    This class provides methods to retrieve a user's top tracks and artists, as well as fetching
    specific tracks and artists by their Spotify ID.

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
    def _create_track(data: dict) -> SpotifyTrack:
        """
        Creates a TopTrack object from Spotify API data.

        Parameters
        ----------
        data : dict
            The track data received from Spotify's API.

        Returns
        -------
        SpotifyTrack
            A validated TopTrack object.

        Raises
        -------
        KeyError
            If a required key is not present within data.
        """

        album = data["album"]
        artist = data["artists"][0]

        track_artist = TrackArtist(id=artist["id"], name=artist["name"])

        top_track = SpotifyTrack(
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
    def _create_artist(data: dict) -> SpotifyArtist:
        """
        Creates a TopArtist object from Spotify API data.

        Parameters
        ----------
        data : dict
            The artist data received from Spotify's API.

        Returns
        -------
        SpotifyArtist
            A validated TopArtist object.

        Raises
        -------
        KeyError
            If a required key is not present within data.
        """

        top_artist = SpotifyArtist(
            id=data["id"],
            name=data["name"],
            images=data["images"],
            spotify_url=data["external_urls"]["music"],
            genres=data["genres"]
        )

        return top_artist

    def _create_item(self, data: dict, item_type: ItemType) -> SpotifyItem:
        """
        Creates a TopItem (TopArtist or TopTrack) object based on the specified item type.

        Parameters
        ----------
        data : dict
            The item data received from Spotify's API.
        item_type : ItemType
            The type of item to create (TRACKS or ARTISTS).

        Returns
        -------
        SpotifyItem
            A validated TopItem object.

        Raises
        ------
        SpotifyDataServiceException
            If a required field is missing, the item type is invalid or data validation fails.
        """

        try:
            if item_type == ItemType.TRACKS:
                return self._create_track(data=data)
            elif item_type == ItemType.ARTISTS:
                return self._create_artist(data=data)
            else:
                raise SpotifyDataServiceException(f"Invalid item_type: {item_type}")
        except KeyError as e:
            missing_key = e.args[0]
            raise SpotifyDataServiceException(
                f"Missing expected key '{missing_key}' in response data for {item_type.value} - {e}"
            )
        except pydantic.ValidationError as e:
            print(f"Failed to create TopItem from Spotify API data - {e}")
            raise SpotifyDataServiceException(
                f"Failed to create TopItem from Spotify API data: {data}, type: {item_type} - {e}"
            )

    async def _get_top_items(
            self,
            access_token: str,
            item_type: ItemType,
            time_range: str,
            limit: int
    ) -> list[SpotifyItem]:
        """
        Fetches a user's top items from Spotify.

        Parameters
        ----------
        access_token : str
            The user's Spotify access token.
        item_type : ItemType
            The type of items to retrieve (TRACKS or ARTISTS).
        time_range : str
            The time range for retrieving top items.
        limit : int
            The number of top items to retrieve.

        Returns
        -------
        list[SpotifyItem]
            A list of the user's top items.

        Raises
        -------
        SpotifyDataServiceException
            If creating the top item objects fails.
        EndpointRequesterUnauthorisedException
            If the Spotify API request returns a 401 Unauthorised response code.
        EndpointRequesterNotFoundException
            If the Spotify API request returns a 404 Not Found response code.
        EndpointRequesterException
            If the Spotify API request fails for any other reason.
        """

        params = {"time_range": time_range, "limit": limit}
        url = f"{self.base_url}/me/top/{item_type.value}?" + urllib.parse.urlencode(params)

        data = await self.endpoint_requester.get(url=url, headers={"Authorization": f"Bearer {access_token}"})

        top_items = [self._create_item(data=entry, item_type=item_type) for entry in data["items"]]

        return top_items

    async def get_top_items(
            self,
            tokens: TokenData,
            item_type: ItemType,
            time_range: TimeRange = TimeRange.MEDIUM,
            limit: int = 20
    ) -> SpotifyItemsResponse:
        """
        Retrieves the top items (tracks or artists) for a user.

        If the request fails due to an expired or invalid token, it attempts to refresh the token and retry.

        Parameters
        ----------
        tokens : TokenData
            The user's access and refresh tokens.
        item_type : ItemType
            The type of items to retrieve (TRACKS or ARTISTS).
        time_range : TimeRange, optional
            The time range for retrieving top items, default is MEDIUM.
        limit : int, optional
            The number of top items to retrieve, default is 20.

        Returns
        -------
        SpotifyItemsResponse
            A response containing the user's top items and most up-to-date access and refresh tokens.

        Raises
        ------
        SpotifyDataServiceException
            If the Spotify API data or token refresh requests fail or response data validation fails.
        """

        try:
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

            top_items_response = SpotifyItemsResponse(data=top_items, tokens=tokens)

            return top_items_response
        except EndpointRequesterException as e:
            raise SpotifyDataServiceException(f"Request to Spotify API failed - {e}")
        except SpotifyAuthServiceException as e:
            raise SpotifyDataServiceException(f"Failed to refresh access token - {e}")

    async def _get_item_by_id(self, access_token: str, item_id: str, item_type: ItemType) -> SpotifyItem:
        """
        Fetches a specific item (track or artist) from the Spotify API using its unique identifier.

        Parameters
        ----------
        access_token : str
            The user's Spotify access token.
        item_id : str
            The unique identifier of the item (track or artist) to retrieve.
        item_type : ItemType
            The type of the item being requested (e.g., TRACKS or ARTISTS).

        Returns
        -------
        SpotifyItem
            An object representing the retrieved track or artist.

        Raises
        ------
        SpotifyDataServiceException
            If creating the top item object fails.
        EndpointRequesterUnauthorisedException
            If the Spotify API request returns a 401 Unauthorised response code.
        EndpointRequesterNotFoundException
            If the Spotify API request returns a 404 Not Found response code.
        EndpointRequesterException
            If the Spotify API request fails for any other reason.
        """

        url = f"{self.base_url}/{item_type.value}/{item_id}"

        data = await self.endpoint_requester.get(url=url, headers={"Authorization": f"Bearer {access_token}"})

        item = self._create_item(data=data, item_type=item_type)

        return item

    async def get_item_by_id(self, item_id: str, tokens: TokenData, item_type: ItemType) -> SpotifyItemResponse:
        """
        Retrieves a specific track or artist by its unique identifier, handling authentication and errors.

        If the request fails due to an expired or invalid token, it attempts to refresh the token and retry.

        Parameters
        ----------
        item_id : str
            The unique identifier of the item (track or artist) to retrieve.
        tokens : TokenData
            The user's authentication tokens required for making the API request.
        item_type : ItemType
            The type of the item being requested (e.g., TRACKS or ARTISTS).

        Returns
        -------
        SpotifyItemResponse
            A response object containing the retrieved item along with updated authentication tokens.

        Raises
        ------
        SpotifyDataServiceNotFoundException
            If the requested item does not exist.
        SpotifyDataServiceException
            If the Spotify API data or token refresh requests fail or response data validation fails.
        """

        try:
            try:
                item = await self._get_item_by_id(
                    item_id=item_id,
                    access_token=tokens.access_token,
                    item_type=item_type
                )
            except EndpointRequesterUnauthorisedException:
                tokens = await self.spotify_auth_service.refresh_tokens(refresh_token=tokens.refresh_token)
                item = await self._get_item_by_id(
                    item_id=item_id,
                    access_token=tokens.access_token,
                    item_type=item_type
                )

            item_response = SpotifyItemResponse(data=item, tokens=tokens)

            return item_response
        except EndpointRequesterNotFoundException:
            raise SpotifyDataServiceNotFoundException(f"Requested item not found - ID: {item_id}, type: {item_type}")
        except EndpointRequesterException as e:
            raise SpotifyDataServiceException(f"Request to Spotify API failed - {e}")
        except SpotifyAuthServiceException as e:
            raise SpotifyDataServiceException(f"Failed to refresh access token - {e}")
