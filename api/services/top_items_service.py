from loguru import logger

from api.data_structures.enums import TopItemType, TopItemTimeRange
from api.data_structures.models import SpotifyItem, SpotifyArtist, SpotifyTrack
from api.services.db_service import DBService, DBServiceException
from api.services.music.spotify_data_service import SpotifyDataService


class TopItemsService:
    def __init__(self, db_service: DBService, spotify_data_service: SpotifyDataService):
        self.db_service = db_service
        self.spotify_data_service = spotify_data_service

    async def _convert_db_items_to_spotify_items(
            self,
            db_items: list[dict],
            item_type: TopItemType
    ) -> list[SpotifyItem]:
        # get spotify item objects
        item_id_field = f"{item_type.value}_id"
        ids = list(map(lambda item: item[item_id_field], db_items))
        spotify_top_items = await self.spotify_data_service.get_many_items_by_ids(
            item_ids=ids,
            item_type=item_type
        )
        item_id_to_top_item_map = {item.id: item for item in spotify_top_items}

        # combine records with item data from spotify
        spotify_items = []

        for db_item in db_items:
            item_id = db_item[item_id_field]
            item_position_change = db_item["position_change"]
            item_is_new = db_item["is_new"]

            item = item_id_to_top_item_map[item_id]

            if item_is_new:
                item.position_change = "new"
            else:
                item.position_change = item_position_change

            spotify_items.append(item)

        return spotify_items

    async def _get_top_items(
            self,
            user_id: str,
            item_type: TopItemType,
            time_range: TopItemTimeRange,
            limit: int
    ) -> list[SpotifyItem]:
        try:
            top_items_db = self.db_service.get_top_items(
                user_id=user_id,
                item_type=item_type,
                time_range=time_range
            )

            if not top_items_db:
                top_items = await self.spotify_data_service.get_top_items(
                    item_type=item_type,
                    time_range=time_range,
                    limit=limit
                )
                return top_items

            top_items = await self._convert_db_items_to_spotify_items(db_items=top_items_db, item_type=item_type)
            return top_items
        except DBServiceException as e:
            error_message = "Failed to retrieve the user's top items from the db"
            logger.error(f"{error_message} - {e}")

            top_items = await self.spotify_data_service.get_top_items(
                item_type=item_type,
                time_range=time_range,
                limit=limit
            )
            return top_items

    async def get_top_artists(self, user_id: str, time_range: TopItemTimeRange, limit: int) -> list[SpotifyArtist]:
        top_items = await self._get_top_items(
            user_id=user_id,
            item_type=TopItemType.ARTIST,
            time_range=time_range,
            limit=limit
        )
        top_artists = [SpotifyArtist(**item.model_dump()) for item in top_items]
        return top_artists
    
    async def get_top_tracks(self, user_id: str, time_range: TopItemTimeRange, limit: int) -> list[SpotifyTrack]:
        top_items = await self._get_top_items(
            user_id=user_id,
            item_type=TopItemType.TRACK,
            time_range=time_range,
            limit=limit
        )
        top_tracks = [SpotifyTrack(**item.model_dump()) for item in top_items]
        return top_tracks
