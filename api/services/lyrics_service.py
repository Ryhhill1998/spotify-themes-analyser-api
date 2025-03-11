import pydantic

from api.models import LyricsRequest, LyricsResponse
from api.services.endpoint_requester import EndpointRequester, EndpointRequesterException


class LyricsServiceException(Exception):
    """
    Exception raised when LyricsService fails to process the API response.

    Parameters
    ----------
    message : str
        The error message describing the failure.
    """

    def __init__(self, message):
        super().__init__(message)


class LyricsServiceNotFoundException(LyricsServiceException):
    """
    Exception raised when LyricsService fails to return results for the request.

    Parameters
    ----------
    message : str
        The error message describing the request for which no results were found.
    """

    def __init__(self, message):
        super().__init__(message)


class LyricsService:
    """
    A service for retrieving track lyrics from an external API.

    This service interacts with an API that provides track lyrics based on track metadata.
    It uses an `EndpointRequester` to send requests and process responses.

    Attributes
    ----------
    base_url : str
        The base URL of the lyrics API.
    endpoint_requester : EndpointRequester
        The service responsible for making HTTP requests.

    Methods
    -------
    get_lyrics_list(lyrics_requests)
        Retrieves lyrics for a list of tracks.
    """

    def __init__(self, base_url: str, endpoint_requester: EndpointRequester):
        """
        Initializes the LyricsService with a base URL and an endpoint requester.

        Parameters
        ----------
        base_url : str
            The base URL of the lyrics API.
        endpoint_requester : EndpointRequester
            An instance of `EndpointRequester` used to make API calls.
        """

        self.base_url = base_url
        self.endpoint_requester = endpoint_requester

    async def get_lyrics_list(self, lyrics_requests: list[LyricsRequest]) -> list[LyricsResponse]:
        """
        Retrieves lyrics for a list of tracks.

        This method sends a POST request to the lyrics API with the provided track details and returns a list of 
        `LyricsResponse` objects containing the lyrics.

        Parameters
        ----------
        lyrics_requests : list[LyricsRequest]
            A list of `LyricsRequest` objects containing the track_id, artist_name and track_title for each track.

        Returns
        -------
        list[LyricsResponse]
            A list of `LyricsResponse` objects containing the track_id, artist_name, track_title and lyrics for each 
            requested track.

        Raises
        ------
        LyricsServiceException
            If the request to the Lyrics API fails or the response fails validation.
        """

        try:
            url = f"{self.base_url}/lyrics-list"

            data = await self.endpoint_requester.post(
                url=url,
                json_data=[item.model_dump() for item in lyrics_requests],
                timeout=None
            )

            return [LyricsResponse(**entry) for entry in data]
        except pydantic.ValidationError as e:
            raise LyricsServiceException(f"Failed to convert API response to LyricsResponse object: {e}")
        except EndpointRequesterException as e:
            raise LyricsServiceException(f"Request to Lyrics API failed - {e}")
