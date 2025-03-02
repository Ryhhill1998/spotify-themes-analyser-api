from api.models import LyricsRequest, LyricsResponse
from api.services.endpoint_requester import EndpointRequester


class LyricsService:
    def __init__(self, base_url: str, endpoint_requester: EndpointRequester):
        self.base_url = base_url
        self.endpoint_requester = endpoint_requester

    async def get_lyrics_list(self, lyrics_requests: list[LyricsRequest]) -> list[LyricsResponse]:
        url = f"{self.base_url}/lyrics-list"

        data = await self.endpoint_requester.post(url=url, json=lyrics_requests, timeout=None)

        lyrics_list = [LyricsResponse(**entry) for entry in data]

        return lyrics_list
