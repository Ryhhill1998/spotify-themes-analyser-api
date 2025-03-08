import pydantic

from api.models import AnalysisRequest, EmotionalProfile
from api.services.endpoint_requester import EndpointRequester


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
    get_emotional_profiles(analysis_requests)
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

    async def get_emotional_profiles(self, analysis_requests: list[AnalysisRequest]) -> list[EmotionalProfile]:
        """
        Retrieves emotional profiles for a list of lyrics.

        This method sends a POST request to the analysis API with the provided list of lyrics and returns a list of
        `EmotionalProfile` objects containing the emotional profile of each track's lyrics.

        Parameters
        ----------
        analysis_requests : list[AnalysisRequest]
            A list of `AnalysisRequest` objects containing the track_id and lyrics for each track.

        Returns
        -------
        list[EmotionalProfile]
            A list of `EmotionalProfile` objects containing the track_id, lyrics and emotional_analysis for each track.

        Raises
        ------
        AnalysisServiceNotFoundException
            If the API returns an empty list.
        AnalysisServiceException
            If the API response cannot be converted into `EmotionalProfile` objects.
        """
        
        url = f"{self.base_url}/emotional-profile"

        data = await self.endpoint_requester.post(
            url=url,
            json_data=[item.model_dump() for item in analysis_requests],
            timeout=None
        )

        if len(data) == 0:
            raise AnalysisServiceNotFoundException(f"No emotional profiles found for request: {analysis_requests}")

        try:
            return [EmotionalProfile(**entry) for entry in data]
        except pydantic.ValidationError as e:
            raise AnalysisServiceException(f"Failed to convert API response to EmotionalProfile object: {e}")
