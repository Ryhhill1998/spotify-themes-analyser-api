import asyncio
from typing import Coroutine

from api.services.endpoint_requester import EndpointRequester


class LyricsService:
    def __init__(self, base_url: str, endpoint_requester: EndpointRequester):
        self.base_url = base_url
        self.endpoint_requester = endpoint_requester

    def _generate_lyrics_request_coroutine(self, params: dict[str, str]) -> Coroutine:
        url = f"{self.base_url}/lyrics"

        coroutine = self.endpoint_requester.get(url=url, params=params)

        return coroutine

    async def get_lyrics(self, track_requested: dict[str, str]) -> dict[str, str]:
        coroutine = self._generate_lyrics_request_coroutine(track_requested)

        data = await coroutine

        return data

    async def get_lyrics_list(self, tracks_requested: list[dict[str, str]]) -> list[dict[str, str]]:
        tasks = []

        for track_req in tracks_requested:
            coroutine = self._generate_lyrics_request_coroutine(track_req)
            tasks.append(coroutine)

        data = await asyncio.gather(*tasks)

        return data
