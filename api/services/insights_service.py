from collections import defaultdict

from api.models import TokenData, LyricsRequest, AnalysisRequest, TopEmotionsResponse, TopEmotion, EmotionalProfile
from api.services.analysis_service import AnalysisService
from api.services.lyrics_service import LyricsService
from api.services.music.spotify_data_service import SpotifyDataService, TopItemType


class InsightsService:
    def __init__(
            self,
            spotify_data_service: SpotifyDataService,
            lyrics_service: LyricsService,
            analysis_service: AnalysisService
    ):
        self.spotify_data_service = spotify_data_service
        self.lyrics_service = lyrics_service
        self.analysis_service = analysis_service

    @staticmethod
    def _aggregate_emotions(emotional_profiles: list[EmotionalProfile]):
        total_emotions = defaultdict(
            lambda: {
                "total": 0,
                "max_track": {"track_id": None, "percentage": 0}
            }
        )

        for profile in emotional_profiles:
            for emotion, percentage in profile.emotional_analysis.model_dump().items():
                total_emotions[emotion]["total"] += percentage

                if percentage > total_emotions[emotion]["max_track"]["percentage"]:
                    total_emotions[emotion]["max_track"] = {"track_id": profile.track_id, "percentage": percentage}

        return total_emotions

    @staticmethod
    def _get_average_emotions(total_emotions: dict, result_count: int) -> list[TopEmotion]:
        return [
            TopEmotion(
                name=emotion,
                percentage=round(info["total"] / result_count, 2),
                track_id=info["max_track"]["track_id"]
            )
            for emotion, info in total_emotions.items()
            if info["max_track"]["track_id"] is not None
        ]

    async def _get_top_emotions(self, analysis_requests: list[AnalysisRequest], limit: int = 5):
        emotional_profiles = await self.analysis_service.get_emotional_profiles(analysis_requests)
        total_emotions = self._aggregate_emotions(emotional_profiles)
        average_emotions = self._get_average_emotions(total_emotions=total_emotions, result_count=len(emotional_profiles))
        top_emotions = sorted(average_emotions, key=lambda e: e.percentage, reverse=True)[:limit]

        return top_emotions

    async def get_top_emotions(self, tokens: TokenData, limit: int = 5) -> TopEmotionsResponse:
        # get top tracks and refreshed tokens (if expired)
        # TODO: Update logic to retrieve top tracks from all 3 time periods for using in emotional profile creation
        top_tracks_response = await self.spotify_data_service.get_top_items(tokens=tokens, item_type=TopItemType.TRACKS)
        data = top_tracks_response.data
        tokens = top_tracks_response.tokens

        # get lyrics for each track
        lyrics_requests = [
            LyricsRequest(
                track_id=entry.id,
                artist_name=entry.artist.name,
                track_title=entry.name
            )
            for entry
            in data
        ]
        lyrics_list = await self.lyrics_service.get_lyrics_list(lyrics_requests)

        # get top emotions for each set of lyrics
        analysis_requests = [AnalysisRequest(track_id=entry.track_id, lyrics=entry.lyrics) for entry in lyrics_list]
        top_emotions = await self._get_top_emotions(analysis_requests, limit=limit)

        # convert top emotions and tokens to emotional profile response object
        emotional_profile_response = TopEmotionsResponse(top_emotions=top_emotions, tokens=tokens)

        return emotional_profile_response
