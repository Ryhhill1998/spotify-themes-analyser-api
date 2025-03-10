from collections import defaultdict

import pydantic

from api.models import TokenData, LyricsRequest, AnalysisRequest, TopEmotionsResponse, TopEmotion, EmotionalProfile
from api.services.analysis_service import AnalysisService, AnalysisServiceException
from api.services.lyrics_service import LyricsService, LyricsServiceException
from api.services.music.spotify_data_service import SpotifyDataService, ItemType, SpotifyDataServiceException


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
            A dictionary where keys are emotion names, and values contain total emotion percentages and the track with
            the highest percentage for that emotion.
        """

        total_emotions = defaultdict(
            lambda: {
                "total": 0,
                "max_track": {"track_id": None, "percentage": 0}
            }
        )

        for profile in emotional_profiles:
            track_id = profile.track_id
            emotional_analysis = profile.emotional_analysis

            for emotion, percentage in emotional_analysis.model_dump().items():
                total_emotions[emotion]["total"] += percentage

                if percentage > total_emotions[emotion]["max_track"]["percentage"]:
                    total_emotions[emotion]["max_track"] = {"track_id": track_id, "percentage": percentage}

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

        Raises
        ------
        InsightsServiceException
            If result_count is less than or equal to 0 or required keys are missing from total_emotions.
        pydantic.ValidationError
            If creating TopEmotion objects fails.
        """

        try:
            if result_count <= 0:
                raise InsightsServiceException("result_count must be positive.")

            return [
                TopEmotion(
                    name=emotion,
                    percentage=round(info["total"] / result_count, 2),
                    track_id=track_id
                )
                for emotion, info in total_emotions.items()
                if (track_id := info["max_track"]["track_id"]) is not None
            ]
        except KeyError as e:
            missing_key = e.args[0]
            raise InsightsServiceException(
                f"Missing expected key '{missing_key}' in total_emotions dict - {e}"
            )

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

        Raises
        ------
        InsightsServiceException
            Raised if any of the services fail to retrieve the requested data or if their responses cannot be converted
            into the appropriate pydantic model.
        """

        if limit <= 0:
            raise InsightsServiceException("Limit must be positive.")

        try:
            # get top tracks and refreshed tokens (if expired)
            top_tracks_response = await self.spotify_data_service.get_top_items(tokens=tokens, item_type=ItemType.TRACKS)
            top_tracks = top_tracks_response.data
            tokens = top_tracks_response.tokens

            if len(top_tracks) == 0:
                raise InsightsServiceException("No top tracks found. Cannot proceed further with analysis.")

            # get lyrics for each track
            lyrics_requests = [
                LyricsRequest(
                    track_id=entry.id,
                    artist_name=entry.artist.name,
                    track_title=entry.name
                )
                for entry
                in top_tracks
            ]

            lyrics_list = await self.lyrics_service.get_lyrics_list(lyrics_requests)

            if len(lyrics_list) == 0:
                raise InsightsServiceException("No lyrics found. Cannot proceed further with analysis.")

            # get top emotions for each set of lyrics
            analysis_requests = [AnalysisRequest(track_id=entry.track_id, lyrics=entry.lyrics) for entry in lyrics_list]

            emotional_profiles = await self.analysis_service.get_emotional_profiles(analysis_requests)

            if len(emotional_profiles) == 0:
                raise InsightsServiceException("No emotional profiles found. Cannot proceed further with analysis.")

            total_emotions = self._aggregate_emotions(emotional_profiles)
            average_emotions = self._get_average_emotions(
                total_emotions=total_emotions,
                result_count=len(emotional_profiles)
            )
            top_emotions = sorted(average_emotions, key=lambda emotion: emotion.percentage, reverse=True)[:limit]

            # convert top emotions and tokens to top emotions response object
            top_emotions_response = TopEmotionsResponse(top_emotions=top_emotions, tokens=tokens)

            return top_emotions_response
        except (SpotifyDataServiceException, LyricsServiceException, AnalysisServiceException) as e:
            raise InsightsServiceException(f"Service failure - {e}")
        except (pydantic.ValidationError, AttributeError) as e:
            raise InsightsServiceException(f"Data validation failure - {e}")
