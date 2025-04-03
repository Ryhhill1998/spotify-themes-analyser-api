from enum import Enum
import urllib.parse
from loguru import logger

import pydantic

from api.models import SpotifyItem, SpotifyTrack, SpotifyArtist, SpotifyTrackArtist, SpotifyTrackData, \
    SpotifyArtistData, SpotifyProfile, SpotifyProfileData
from api.services.endpoint_requester import EndpointRequester, EndpointRequesterUnauthorisedException, \
    EndpointRequesterException, EndpointRequesterNotFoundException
from api.services.music.music_service import MusicService
from api.services.music.spotify_auth_service import SpotifyAuthService


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
        

class SpotifyDataServiceUnauthorisedException(SpotifyDataServiceException):
    """
    Exception raised when SpotifyDataService fails to authenticate the request with the provided access_token.

    Parameters
    ----------
    message : str
        The error message describing the resource that was not found.
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

    Methods
    -------
    get_top_items(tokens, item_type, time_range=TimeRange.MEDIUM, limit=20) -> SpotifyItemsResponse
        Retrieves the top tracks or artists for a user.

    get_item_by_id(item_id, tokens, item_type) -> SpotifyItemResponse
        Retrieves a specific track or artist by its unique identifier, handling authentication and errors.
    """

    def __init__(
            self,
            client_id: str,
            client_secret: str,
            base_url: str,
            endpoint_requester: EndpointRequester
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
        """

        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            base_url=base_url,
            endpoint_requester=endpoint_requester
        )

    async def get_profile_data(self, access_token: str) -> SpotifyProfile:
        """
            Fetches a user's profile from Spotify.

            Parameters
            ----------
            access_token : str
                The user's Spotify access token.

            Returns
            -------
            SpotifyProfile
                The user's Spotify profile data.

            Raises
            -------
            SpotifyDataServiceUnauthorisedException
                If the Spotify API request returns a 401 Unauthorised response code.
            SpotifyDataServiceException
                If the Spotify API request fails for any other reason or API data validation fails.
            """

        try:
            url = f"{self.base_url}/me"

            data = await self.endpoint_requester.get(url=url, headers={"Authorization": f"Bearer {access_token}"})

            profile_data = SpotifyProfileData(**data)

            return SpotifyProfile(
                id=profile_data.id,
                display_name=profile_data.display_name,
                email=profile_data.email,
                href=profile_data.href,
                images=profile_data.images,
                followers=profile_data.followers.total
            )
        except EndpointRequesterUnauthorisedException as e:
            error_message = "Invalid Spotify API access token"
            logger.error(f"{error_message} - {e}")
            raise SpotifyDataServiceUnauthorisedException(error_message)
        except EndpointRequesterException as e:
            error_message = "Failed to make request to Spotify API"
            logger.error(f"{error_message} - {e}")
            raise SpotifyDataServiceException(error_message)
        except pydantic.ValidationError as e:
            error_message = "Spotify API data validation failed"
            logger.error(f"{error_message} - {e}")
            raise SpotifyDataServiceException(error_message)

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
        TypeError
            If data is not a dict.
        pydantic.ValidationError
            If data validation fails.
        """

        track_data = SpotifyTrackData(**data)

        artist = track_data.artists[0]
        track_artist = SpotifyTrackArtist(id=artist.id, name=artist.name)
        album = track_data.album

        top_track = SpotifyTrack(
            id=track_data.id,
            name=track_data.name,
            images=album.images,
            album_name=album.name,
            spotify_url=track_data.external_urls.spotify,
            artist=track_artist,
            release_date=album.release_date,
            explicit=track_data.explicit,
            duration_ms=track_data.duration_ms,
            popularity=track_data.popularity
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
        TypeError
            If data is not a dict.
        pydantic.ValidationError
            If data validation fails.
        """

        artist_data = SpotifyArtistData(**data)

        top_artist = SpotifyArtist(
            id=artist_data.id,
            name=artist_data.name,
            images=artist_data.images,
            spotify_url=artist_data.external_urls.spotify,
            genres=artist_data.genres,
            followers=artist_data.followers.total,
            popularity=artist_data.popularity
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
                error_message = f"Invalid item_type: {item_type}"
                logger.error(error_message)
                raise SpotifyDataServiceException(error_message)
        except TypeError as e:
            error_message = f"Spotify data not of type dict. Actual type: {type(data)} - {e}"
            logger.error(error_message)
            raise SpotifyDataServiceException(error_message)
        except pydantic.ValidationError as e:
            error_message = f"Failed to create TopItem from Spotify API data: {data}, type: {item_type} - {e}"
            logger.error(error_message)
            raise SpotifyDataServiceException(error_message)

    async def get_top_items(
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
        SpotifyDataServiceUnauthorisedException
            If the Spotify API request returns a 401 Unauthorised response code.
        SpotifyDataServiceException
                If the Spotify API request fails for any other reason or API data validation fails.
        """

        try:
            params = {"time_range": time_range, "limit": limit}
            url = f"{self.base_url}/me/top/{item_type.value}?" + urllib.parse.urlencode(params)

            data = await self.endpoint_requester.get(url=url, headers={"Authorization": f"Bearer {access_token}"})

            top_items = [self._create_item(data=entry, item_type=item_type) for entry in data["items"]]

            return top_items
        except EndpointRequesterUnauthorisedException as e:
            error_message = "Invalid Spotify API access token"
            logger.error(f"{error_message} - {e}")
            raise SpotifyDataServiceUnauthorisedException(error_message)
        except EndpointRequesterException as e:
            error_message = "Failed to make request to Spotify API"
            logger.error(f"{error_message} - {e}")
            raise SpotifyDataServiceException(error_message)

    async def get_item_by_id(self, access_token: str, item_id: str, item_type: ItemType) -> SpotifyItem:
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
            If creating the top item object or the API request fails.
        SpotifyDataServiceUnauthorisedException
            If the Spotify API request returns a 401 Unauthorised response code.
        SpotifyDataServiceNotFoundException
            If the Spotify API request returns a 404 Not Found response code.
        """

        try:
            url = f"{self.base_url}/{item_type.value}/{item_id}"

            data = await self.endpoint_requester.get(url=url, headers={"Authorization": f"Bearer {access_token}"})

            item = self._create_item(data=data, item_type=item_type)

            return item
        except EndpointRequesterUnauthorisedException as e:
            error_message = "Invalid Spotify API access token"
            logger.error(f"{error_message} - {e}")
            raise SpotifyDataServiceUnauthorisedException(error_message)
        except EndpointRequesterNotFoundException as e:
            error_message = f"Requested Spotify item not found. Item ID: {item_id}, item type: {item_type}"
            logger.error(f"{error_message} - {e}")
            raise SpotifyDataServiceNotFoundException(error_message)
        except EndpointRequesterException as e:
            error_message = "Failed to make request to Spotify API"
            logger.error(f"{error_message} - {e}")
            raise SpotifyDataServiceException(error_message)
