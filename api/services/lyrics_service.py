import asyncio

import pydantic
from loguru import logger

from api.data_structures.models import LyricsRequest, LyricsResponse
from api.services.endpoint_requester import EndpointRequester, EndpointRequesterException, \
    EndpointRequesterNotFoundException


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
    It uses an `EndpointRequester` to send requests and process responses asynchronously.

    Attributes
    ----------
    base_url : str
        The base URL of the lyrics API.
    endpoint_requester : EndpointRequester
        The service responsible for making HTTP requests.

    Methods
    -------
    get_lyrics(lyrics_request)
        Retrieves the lyrics for a single track.
    get_lyrics_list(lyrics_requests)
        Retrieves lyrics for multiple tracks asynchronously.
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

    async def get_lyrics(self, lyrics_request: LyricsRequest) -> LyricsResponse:
        """
        Retrieves the lyrics for a single track.

        This method sends a POST request to the lyrics API with the provided track metadata
        and returns a `LyricsResponse` object containing the lyrics.

        Parameters
        ----------
        lyrics_request : LyricsRequest
            The `LyricsRequest` object containing the track_id, artist_name and track_title.

        Returns
        -------
        LyricsResponse
            A `LyricsResponse` object containing the track_id, artist_name, track_title and lyrics.

        Raises
        ------
        LyricsServiceException
            If the request to the lyrics API fails or the response fails validation.
        """

        try:
            url = f"{self.base_url}/lyrics"

            data = await self.endpoint_requester.post(
                url=url,
                json_data=lyrics_request.model_dump(),
                timeout=None
            )

            lyrics_response = LyricsResponse(**data)

            return lyrics_response
        except pydantic.ValidationError as e:
            error_message = f"Failed to convert API response to LyricsResponse object - {e}"
            logger.error(error_message)
            raise LyricsServiceException(error_message)
        except EndpointRequesterNotFoundException as e:
            error_message = (
                f"Requested lyrics not found for track_id: {lyrics_request.track_id}, "
                f"artist_name: {lyrics_request.artist_name}, track_title: {lyrics_request.track_title} - {e}"
            )
            logger.error(error_message)
            raise LyricsServiceNotFoundException(error_message)
        except EndpointRequesterException as e:
            error_message = f"Request to Lyrics API failed - {e}"
            logger.error(error_message)
            raise LyricsServiceException(error_message)

    def _create_lyrics_tasks(self, requests: list[LyricsRequest]):
        """
        Creates a list of coroutines for retrieving lyrics.

        Parameters
        ----------
        requests : list[LyricsRequest]
            A list of lyrics requests.

        Returns
        -------
        list[asyncio.Task]
            A list of tasks that can be awaited.
        """
        return [self.get_lyrics(req) for req in requests]

    async def get_lyrics_list(self, lyrics_requests: list[LyricsRequest]) -> list[LyricsResponse]:
        """
        Retrieves lyrics for a multiple tracks asynchronously.

        This method sends multiple POST requests concurrently to fetch lyrics for a batch of tracks.

        Parameters
        ----------
        lyrics_requests : list[LyricsRequest]
            A list of `LyricsRequest` objects containing the track_id, artist_name and track_title for each track.

        Returns
        -------
        list[LyricsResponse]
            A list of `LyricsResponse` objects containing the track_id, artist_name, track_title and lyrics for each 
            requested track.

        Notes
        -----
        - This method uses asyncio.gather() to perform concurrent requests.
        - If some requests fail, only successful responses will be returned.
        """

        tasks = self._create_lyrics_tasks(lyrics_requests)
        lyrics_list = await asyncio.gather(*tasks, return_exceptions=True)
        successful_results = [item for item in lyrics_list if isinstance(item, LyricsResponse)]

        logger.info(f"Retrieved lyrics for {len(successful_results)}/{len(lyrics_list)} tracks.")

        return successful_results
