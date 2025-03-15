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
    A service for retrieving emotional profile analyses of track lyrics from an external API.

    This service interacts with an API that provides emotional profile analyses of track lyrics.
    It uses an `EndpointRequester` to send requests and process responses.

    Attributes
    ----------
    base_url : str
        The base URL of the analysis API.
    endpoint_requester : EndpointRequester
        The service responsible for making HTTP requests.

    Methods
    -------
    get_emotional_profiles_list(requests)
        Retrieves emotional profiles for a list of lyrics.
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
        Retrieves emotional profiles for a list of lyrics.

        This method sends a POST request to the analysis API with the provided list of lyrics and returns a list of
        `EmotionalProfile` objects containing the emotional profile of each track's lyrics.

        Parameters
        ----------
        requests : list[EmotionalProfileRequest]
            A list of `AnalysisRequest` objects containing the track_id and lyrics for each track.

        Returns
        -------
        list[EmotionalProfileResponse]
            A list of `EmotionalProfile` objects containing the track_id, lyrics and emotional_analysis for each track.

        Raises
        ------
        AnalysisServiceException
            If the request to the analysis API fails or the response fails validation.
        """

        tasks = [self.get_emotional_profile(req) for req in requests]
        emotional_profiles = await asyncio.gather(*tasks, return_exceptions=True)
        successful_results = [item for item in emotional_profiles if isinstance(item, EmotionalProfileResponse)]

        print(f"Retrieved analysis for {len(successful_results)}/{len(emotional_profiles)} tracks.")

        return successful_results
