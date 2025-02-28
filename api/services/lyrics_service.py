import asyncio
from typing import Coroutine

from api.models import TrackRequest, LyricsResponse
from api.services.endpoint_requester import EndpointRequester


class LyricsService:
    def __init__(self, base_url: str, endpoint_requester: EndpointRequester):
        self.base_url = base_url
        self.endpoint_requester = endpoint_requester

    def _generate_lyrics_request_coroutine(self, track_requested: TrackRequest) -> Coroutine:
        params = {"artist": track_requested["artist"], "track_title": track_requested["track_title"]}
        url = f"{self.base_url}/lyrics"

        coroutine = self.endpoint_requester.get(url=url, params=params)

        return coroutine

    async def get_lyrics(self, track_requested: TrackRequest) -> LyricsResponse:
        coroutine = self._generate_lyrics_request_coroutine(track_requested)

        data = await coroutine

        lyrics = LyricsResponse(**data)
        return lyrics

    async def get_lyrics_list(self, tracks_requested: list[TrackRequest]) -> list[LyricsResponse]:
        tasks = []

        for track_req in tracks_requested:
            coroutine = self._generate_lyrics_request_coroutine(track_req)
            tasks.append(coroutine)

        data = await asyncio.gather(*tasks)

        lyrics_list = [LyricsResponse(**entry) for entry in data]
        return lyrics_list
