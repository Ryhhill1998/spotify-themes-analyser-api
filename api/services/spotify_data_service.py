from enum import Enum
import urllib.parse
import requests

from api.services.spotify_service import SpotifyService


class TopItemType(Enum):
    ARTISTS = "artists"
    TRACKS = "tracks"


class SpotifyDataService(SpotifyService):
    def __init__(self, client_id: str, client_secret: str, base_url: str):
        super().__init__(client_id=client_id, client_secret=client_secret, base_url=base_url)

    def get_top_items(
            self,
            access_token: str,
            item_type: TopItemType,
            time_range: str = "medium_term",
            limit: int = 10
    ) -> list:
        params = {"time_range": time_range, "limit": limit}
        url = f"{self.base_url}/me/top/{item_type}?" + urllib.parse.urlencode(params)

        res = requests.get(url=url, headers={"Authorization": f"Bearer {access_token}"})

        res.raise_for_status()

        return res.json()
