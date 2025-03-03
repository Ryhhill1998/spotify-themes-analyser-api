from enum import Enum
import urllib.parse

from httpx import HTTPStatusError

from api.models import TopItemsResponse, TopItem, TopTrack, TopArtist, TokenData
from api.services.endpoint_requester import EndpointRequester
from api.services.spotify.spotify_auth_service import SpotifyAuthService
from api.services.spotify.spotify_service import SpotifyService


class TopItemType(Enum):
    ARTISTS = "artists"
    TRACKS = "tracks"


class TimeRange(Enum):
    SHORT = "short_term"
    MEDIUM = "medium_term"
    LONG = "long_term"


class SpotifyDataService(SpotifyService):
    def __init__(
            self,
            client_id: str,
            client_secret: str,
            base_url: str,
            endpoint_requester: EndpointRequester,
            spotify_auth_service: SpotifyAuthService
    ):
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            base_url=base_url,
            endpoint_requester=endpoint_requester
        )
        self.spotify_auth_service = spotify_auth_service

    @staticmethod
    def _create_top_track_object(data: dict) -> TopTrack:
        album = data["album"]

        top_track = TopTrack(
            id=data["id"],
            name=data["name"],
            images=album["images"],
            spotify_url=data["external_urls"]["spotify"],
            artist=data["artists"][0]["name"],
            release_date=album["release_date"],
            explicit=data["explicit"],
            duration_ms=data["duration_ms"],
            popularity=data["popularity"]
        )

        return top_track

    @staticmethod
    def _create_top_artist_object(data: dict) -> TopArtist:
        top_artist = TopArtist(
            id=data["id"],
            name=data["name"],
            images=data["images"],
            spotify_url=data["external_urls"]["spotify"],
            genres=data["genres"]
        )

        return top_artist

    def _create_top_item_objects(self, data: list[dict], item_type: TopItemType) -> list[TopItem]:
        if item_type == TopItemType.TRACKS:
            return [self._create_top_track_object(data=entry) for entry in data]
        elif item_type == TopItemType.ARTISTS:
            return [self._create_top_artist_object(data=entry) for entry in data]
        else:
            raise ValueError("Invalid item type.")

    async def _get_top_items(
            self,
            access_token: str,
            item_type: TopItemType,
            time_range: str,
            limit: int
    ) -> list[TopItem]:
        params = {"time_range": time_range, "limit": limit}
        url = f"{self.base_url}/me/top/{item_type.value}?" + urllib.parse.urlencode(params)

        data = await self.endpoint_requester.get(url=url, headers={"Authorization": f"Bearer {access_token}"})

        top_items = self._create_top_item_objects(data=data["items"], item_type=item_type)

        return top_items

    async def get_top_items(
            self,
            tokens: TokenData,
            item_type: TopItemType,
            time_range: TimeRange = TimeRange.MEDIUM,
            limit: int = 10
    ) -> TopItemsResponse:
        try:
            top_items = await self._get_top_items(
                access_token=tokens.access_token,
                item_type=item_type,
                time_range=time_range.value,
                limit=limit
            )
        except HTTPStatusError as e:
            if e.response.status_code == 401:
                tokens = await self.spotify_auth_service.refresh_tokens(refresh_token=tokens.refresh_token)

                top_items = await self._get_top_items(
                    access_token=tokens.access_token,
                    item_type=item_type,
                    time_range=time_range.value,
                    limit=limit
                )
            else:
                raise

        return TopItemsResponse(data=top_items, tokens=tokens)
