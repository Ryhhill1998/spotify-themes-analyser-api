from collections import defaultdict

import pydantic

from api.models import TokenData, LyricsRequest, AnalysisRequest, TopEmotionsResponse, TopEmotion, EmotionalProfile
from api.services.analysis_service import AnalysisService
from api.services.lyrics_service import LyricsService
from api.services.music.spotify_data_service import SpotifyDataService, TopItemType


class InsightsServiceException(Exception):
    """
    Exception raised when InsightsService fails to process the responses from the services.

    Parameters
    ----------
    message : str
        The error message describing the failure.
    """

    def __init__(self, message):
        super().__init__(message)


class InsightsService:
    """
    A service for analyzing emotional profiles of top tracks.

    This service retrieves the user's top tracks from Spotify, fetches their lyrics,
    analyzes the lyrics for emotional content, and aggregates the results to determine
    the most prominent emotions.

    Attributes
    ----------
    spotify_data_service : SpotifyDataService
        The service responsible for fetching top tracks from Spotify.
    lyrics_service : LyricsService
        The service responsible for retrieving song lyrics.
    analysis_service : AnalysisService
        The service responsible for analyzing song lyrics for emotional content.

    Methods
    -------
    get_top_emotions(tokens, limit=5)
        Retrieves the top emotions detected in a user's top tracks.
    """

    def __init__(
            self,
            spotify_data_service: SpotifyDataService,
            lyrics_service: LyricsService,
            analysis_service: AnalysisService
    ):
        """
        Initializes the InsightsService with dependencies for retrieving music data,
        fetching lyrics, and performing emotional analysis.

        Parameters
        ----------
        spotify_data_service : SpotifyDataService
            An instance of `SpotifyDataService` used to retrieve a user's top tracks.
        lyrics_service : LyricsService
            An instance of `LyricsService` used to fetch lyrics for songs.
        analysis_service : AnalysisService
            An instance of `AnalysisService` used to analyze song lyrics for emotional content.
        """

        self.spotify_data_service = spotify_data_service
        self.lyrics_service = lyrics_service
        self.analysis_service = analysis_service

    @staticmethod
    def _aggregate_emotions(emotional_profiles: list[EmotionalProfile]) -> dict:
        """
        Aggregates emotional analysis results across multiple songs.

        This method sums up emotion percentages and tracks the song with the highest percentage for each emotion.

        Parameters
        ----------
        emotional_profiles : list[EmotionalProfile]
            A list of `EmotionalProfile` objects containing emotional analysis results.

        Returns
        -------
        dict
            A dictionary where keys are emotion names, and values contain total emotion percentages
            and the track with the highest percentage for that emotion.
        """

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
        """
        Computes the average percentage for each emotion across all analyzed tracks.

        Parameters
        ----------
        total_emotions : dict
            A dictionary containing total emotion percentages and the highest contributing track.
        result_count : int
            The total number of tracks analyzed.

        Returns
        -------
        list[TopEmotion]
            A list of `TopEmotion` objects representing the averaged emotional profile.
        """

        try:
            return [
                TopEmotion(
                    name=emotion,
                    percentage=round(info["total"] / result_count, 2),
                    track_id=info["max_track"]["track_id"]
                )
                for emotion, info in total_emotions.items()
                if info["max_track"]["track_id"] is not None
            ]
        except pydantic.ValidationError as e:
            raise InsightsServiceException(
                f"Failed to convert total_emotions to TopEmotion list: {e}"
            )

    async def _get_top_emotions(self, analysis_requests: list[AnalysisRequest], limit: int = 5):
        """
        Retrieves and processes emotional profiles for a set of lyrics.

        Parameters
        ----------
        analysis_requests : list[AnalysisRequest]
            A list of `AnalysisRequest` objects containing lyrics to be analyzed.
        limit : int, optional
            The number of top emotions to return (default is 5).

        Returns
        -------
        list[TopEmotion]
            A sorted list of `TopEmotion` objects representing the most prominent emotions.
        """

        emotional_profiles = await self.analysis_service.get_emotional_profiles(analysis_requests)
        result_count = len(emotional_profiles)
        total_emotions = self._aggregate_emotions(emotional_profiles)
        average_emotions = self._get_average_emotions(total_emotions=total_emotions, result_count=result_count)
        top_emotions = sorted(average_emotions, key=lambda e: e.percentage, reverse=True)[:limit]

        return top_emotions

    async def get_top_emotions(self, tokens: TokenData, limit: int = 5) -> TopEmotionsResponse:
        """
        Retrieves the top emotions detected in a user's top Spotify tracks.

        This method fetches a user's top tracks from Spotify, retrieves lyrics for each track,
        performs emotional analysis, and returns the most prominent emotions.

        Parameters
        ----------
        tokens : TokenData
            The authentication tokens required to access the Spotify API.
        limit : int, optional
            The number of top emotions to return (default is 5).

        Returns
        -------
        TopEmotionsResponse
            An object containing the top detected emotions and refreshed authentication tokens.
        """

        # get top tracks and refreshed tokens (if expired)
        # TODO: Update logic to retrieve top tracks from all 3 time periods for using in emotional profile creation
        top_tracks_response = await self.spotify_data_service.get_top_items(tokens=tokens, item_type=TopItemType.TRACKS)
        top_tracks = top_tracks_response.data
        tokens = top_tracks_response.tokens

        # get lyrics for each track
        try:
            lyrics_requests = [
                LyricsRequest(
                    track_id=entry.id,
                    artist_name=entry.artist.name,
                    track_title=entry.name
                )
                for entry
                in top_tracks
            ]
        except pydantic.ValidationError as e:
            raise InsightsServiceException(
                f"Failed to convert spotify_data_service response to LyricsRequest list: {e}"
            )

        lyrics_list = await self.lyrics_service.get_lyrics_list(lyrics_requests)

        # get top emotions for each set of lyrics
        try:
            analysis_requests = [AnalysisRequest(track_id=entry.track_id, lyrics=entry.lyrics) for entry in lyrics_list]
        except pydantic.ValidationError as e:
            raise InsightsServiceException(
                f"Failed to convert lyrics_service response to AnalysisRequest list: {e}"
            )

        top_emotions = await self._get_top_emotions(analysis_requests, limit=limit)

        # convert top emotions and tokens to emotional profile response object
        try:
            emotional_profile_response = TopEmotionsResponse(top_emotions=top_emotions, tokens=tokens)
        except pydantic.ValidationError as e:
            raise InsightsServiceException(
                f"Failed to convert top_emotions to TopEmotionsResponse: {e}"
            )

        return emotional_profile_response
