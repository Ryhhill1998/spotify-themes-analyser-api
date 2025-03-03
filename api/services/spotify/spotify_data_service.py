from enum import Enum
import urllib.parse

from httpx import HTTPStatusError

from api.models import TopItemsResponse, TopItem, TopTrack, TopArtist
from api.services.endpoint_requester import EndpointRequester
from api.services.spotify.spotify_auth_service import SpotifyAuthService
from api.services.spotify.spotify_service import SpotifyService


class TopItemType(Enum):
    ARTISTS = "artists"
    TRACKS = "tracks"


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

    async def _get_top_items(
            self,
            access_token: str,
            item_type: TopItemType,
            time_range: str = "medium_term",
            limit: int = 10
    ) -> list[dict[str, str]]:
        params = {"time_range": time_range, "limit": limit}
        url = f"{self.base_url}/me/top/{item_type.value}?" + urllib.parse.urlencode(params)

        data = await self.endpoint_requester.get(url=url, headers={"Authorization": f"Bearer {access_token}"})

        return data

    @staticmethod
    def _create_top_track_object(data: dict) -> TopTrack:
        album = data["album"]

        top_track = TopTrack(
            id=data["id"],
            name=data["name"],
            image_urls=album["images"],
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
            image_urls=data["album"]["images"],
            spotify_url=data["external_urls"]["spotify"]
        )

        return top_artist

    def _create_top_item_object(self, data: dict, item_type: TopItemType) -> TopItem:
        if item_type.value == TopItemType.TRACKS:
            return self._create_top_track_object(data)
        elif item_type.value == TopItemType.ARTISTS:
            return self._create_top_artist_object(data)
        else:
            raise ValueError("Invalid item type.")

    async def get_top_items(
            self,
            access_token: str,
            refresh_token: str,
            item_type: TopItemType,
            time_range: str = "medium_term",
            limit: int = 10
    ) -> TopItemsResponse:
        try:
            data = await self._get_top_items(
                access_token=access_token,
                item_type=item_type,
                time_range=time_range,
                limit=limit
            )
        except HTTPStatusError as e:
            if e.response.status_code == 401:
                refresh_data = await self.spotify_auth_service.refresh_access_token(refresh_token=refresh_token)
                access_token = refresh_data["access_token"]
                refresh_token = refresh_data["refresh_token"]

                data = await self._get_top_items(
                    access_token=access_token,
                    item_type=item_type,
                    time_range=time_range,
                    limit=limit
                )
            else:
                raise

        top_items = [self._create_top_item_object(data=entry, item_type=item_type) for entry in data]

        return TopItemsResponse(data=top_items, access_token=access_token, refresh_token=refresh_token)
