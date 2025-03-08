from api.models import AnalysisRequest, EmotionalProfile
from api.services.endpoint_requester import EndpointRequester


class AnalysisServiceException(Exception):
    """Raised when AnalysisService fails to process the API response."""

    def __init__(self, message):
        super().__init__(message)


class AnalysisService:
    def __init__(self, base_url: str, endpoint_requester: EndpointRequester):
        """
        Service for retrieving emotional profiles from an external API.

        Args:
            base_url (str): The base URL of the API.
            endpoint_requester (EndpointRequester): Handles API requests.
        """

        self.base_url = base_url
        self.endpoint_requester = endpoint_requester

    async def get_emotional_profiles(self, analysis_requests: list[AnalysisRequest]) -> list[EmotionalProfile]:
        """
        Fetches emotional profiles for a list of tracks from external API.

        Args:
            analysis_requests (list[AnalysisRequest]): List of analysis requests.

        Returns:
            list[EmotionalProfile]: List of emotional profiles.

        Raises:
            AnalysisServiceException: If response parsing fails.
        """

        url = f"{self.base_url}/emotional-profile"

        data = await self.endpoint_requester.post(
            url=url,
            json_data=[item.model_dump() for item in analysis_requests],
            timeout=None
        )

        try:
            return [EmotionalProfile(**entry) for entry in data]
        except Exception as e:
            raise AnalysisServiceException(f"Failed to process API response: {e}")
