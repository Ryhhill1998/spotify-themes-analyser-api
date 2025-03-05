from api.models import TokenData, LyricsRequest, AnalysisRequest, EmotionalProfileResponse
from api.services.analysis_service import AnalysisService
from api.services.lyrics_service import LyricsService
from api.services.spotify.spotify_data_service import SpotifyDataService, TopItemType


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

    async def get_emotional_profile(self, tokens: TokenData, limit: int = 5) -> EmotionalProfileResponse:
        # get top tracks and refreshed tokens (if expired)
        top_tracks_response = await self.spotify_data_service.get_top_items(tokens=tokens, item_type=TopItemType.TRACKS)
        data = top_tracks_response.data
        tokens = top_tracks_response.tokens

        # get lyrics each track
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
        top_emotions = await self.analysis_service.get_top_emotions(analysis_requests, limit=limit)

        # convert top emotions and tokens to emotional profile response object
        emotional_profile_response = EmotionalProfileResponse(emotions=top_emotions, tokens=tokens)

        return emotional_profile_response
