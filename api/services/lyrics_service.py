from api.models import LyricsRequest, LyricsResponse
from api.services.endpoint_requester import EndpointRequester

class LyricsServiceException(Exception):
    """Raised when LyricsService fails to process the API response."""
    def __init__(self, message):
        super().__init__(message)

class LyricsService:
    def __init__(self, base_url: str, endpoint_requester: EndpointRequester):
        self.base_url = base_url
        self.endpoint_requester = endpoint_requester

    async def get_lyrics_list(self, lyrics_requests: list[LyricsRequest]) -> list[LyricsResponse]:
        url = f"{self.base_url}/lyrics-list"

        data = await self.endpoint_requester.post(
            url=url,
            json_data=[item.model_dump() for item in lyrics_requests],
            timeout=None
        )

        try:
            return [LyricsResponse(**entry) for entry in data]
        except Exception as e:
            raise LyricsServiceException(f"Failed to convert API response: {e}")
