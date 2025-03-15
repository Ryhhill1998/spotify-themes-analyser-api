import asyncio

import pydantic

from api.models import EmotionalProfileResponse, EmotionalTagsResponse, EmotionalTagsRequest, EmotionalProfileRequest
from api.services.endpoint_requester import EndpointRequester, EndpointRequesterException


class AnalysisServiceException(Exception):
    """
    Raised when AnalysisService fails to process the API response.
    
    Parameters
    ----------
    message : str
        The error message describing the failure.
    """

    def __init__(self, message):
        super().__init__(message)


class AnalysisServiceNotFoundException(AnalysisServiceException):
    """
    Exception raised when AnalysisService fails to return results for the request.

    Parameters
    ----------
    message : str
        The error message describing the request for which no results were found.
    """

    def __init__(self, message):
        super().__init__(message)


class AnalysisService:
    """
    A service for interacting with the analysis API to retrieve emotional tags and emotional profiles of lyrics.

    This class provides methods to analyze lyrics by making API calls and processing responses into structured objects.

    Attributes
    ----------
    base_url : str
        The base URL of the analysis API.
    endpoint_requester : EndpointRequester
        The service responsible for making HTTP requests.

    Methods
    -------
    get_emotional_tags(request)
        Retrieves emotional tags for the given lyrics.
    get_emotional_profile(request)
        Retrieves the emotional profile of a track’s lyrics.
    get_emotional_profiles_list(requests)
        Retrieves emotional profiles for multiple tracks concurrently (async).
    """
    
    def __init__(self, base_url: str, endpoint_requester: EndpointRequester):
        """
        Initializes the AnalysisService with a base URL and an endpoint requester.

        Parameters
        ----------
        base_url : str
            The base URL of the analysis API.
        endpoint_requester : EndpointRequester
            An instance of `EndpointRequester` used to make API calls.
        """
        
        self.base_url = base_url
        self.endpoint_requester = endpoint_requester

    async def get_emotional_tags(self, request: EmotionalTagsRequest) -> EmotionalTagsResponse:
        """
        Retrieves emotional tags associated with a track's lyrics.

        This method sends a POST request to the analysis API with the provided lyrics and returns an
        `EmotionalTagsResponse` containing the track_id and lyrics. The lyrics string is HTML containing span tags
        with a class of the requested emotion surrounding words and phrases displaying this emotion.

        E.g. 'I don't want to be another memory<br/>I want to be a <span class="anger">haunting reminder</span>'

        Parameters
        ----------
        request : EmotionalTagsRequest
            The `EmotionalTagsRequest` object containing the track_id and lyrics for emotional tagging.

        Returns
        -------
        EmotionalTagsResponse
            An object containing the track_id and the lyrics containing emotional tags.

        Raises
        ------
        AnalysisServiceException
            If the request to the analysis API fails or the response fails validation.
        """

        try:
            url = f"{self.base_url}/emotional-tags"

            data = await self.endpoint_requester.post(
                url=url,
                json_data=request.model_dump(),
                timeout=None
            )

            emotional_tags_response = EmotionalTagsResponse(**data)

            return emotional_tags_response
        except pydantic.ValidationError as e:
            print(e)
            raise AnalysisServiceException(f"Failed to convert API response to EmotionalTagsResponse object: {e}")
        except EndpointRequesterException as e:
            print(e)
            raise AnalysisServiceException(f"Request to Analysis API failed - {e}")

    async def get_emotional_profile(self, request: EmotionalProfileRequest) -> EmotionalProfileResponse:
        """
        Retrieves the emotional profile of a track's lyrics.

        This method sends a POST request to the analysis API with the provided track_id and lyrics and returns an
        `EmotionalProfileResponse` object containing the track_id, lyrics and emotional_profile of the track.

        Parameters
        ----------
        request : EmotionalProfileRequest
            The `EmotionalProfileRequest` object containing the track_id and lyrics.

        Returns
        -------
        EmotionalProfileResponse
            An `EmotionalProfileResponse` object containing the track_id, lyrics and emotional_profile.

        Raises
        ------
        AnalysisServiceException
            If the request to the analysis API fails or the response fails validation.
        """

        try:
            url = f"{self.base_url}/emotional-profile"

            data = await self.endpoint_requester.post(
                url=url,
                json_data=request.model_dump(),
                timeout=None
            )

            emotional_profile_response = EmotionalProfileResponse(**data)

            return emotional_profile_response
        except pydantic.ValidationError as e:
            print(e)
            raise AnalysisServiceException(f"Failed to convert API response to EmotionalProfile object: {e}")
        except EndpointRequesterException as e:
            print(e)
            raise AnalysisServiceException(f"Request to Analysis API failed - {e}")

    async def get_emotional_profiles_list(self, requests: list[EmotionalProfileRequest]) -> list[EmotionalProfileResponse]:
        """
        Retrieves emotional profiles for multiple tracks asynchronously.

        This method sends multiple POST requests concurrently to fetch emotional profiles for a batch of tracks.

        Parameters
        ----------
        requests : list[EmotionalProfileRequest]
            A list of `EmotionalProfileRequest` objects containing track_ids and lyrics.

        Returns
        -------
        list[EmotionalProfileResponse]
            A list of `EmotionalProfileResponse` objects containing emotional profiles of each track.

        Notes
        -----
        - This method uses asyncio.gather() to perform concurrent requests.
        - If some requests fail, only successful responses will be returned.
        """

        tasks = [self.get_emotional_profile(req) for req in requests]
        emotional_profiles = await asyncio.gather(*tasks, return_exceptions=True)
        successful_results = [item for item in emotional_profiles if isinstance(item, EmotionalProfileResponse)]

        print(f"Retrieved analysis for {len(successful_results)}/{len(emotional_profiles)} tracks.")

        return successful_results
