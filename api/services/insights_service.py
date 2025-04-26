from collections import defaultdict

import pydantic
from loguru import logger

from api.data_structures.enums import TopItemTimeRange, TopItemType
from api.data_structures.models import LyricsRequest, TopEmotion, EmotionalProfileResponse, EmotionalProfileRequest, \
    EmotionalTagsRequest, Emotion, SpotifyTrack, EmotionalTagsResponse
from api.services.analysis_service import AnalysisService, AnalysisServiceException
from api.services.lyrics_service import LyricsService, LyricsServiceException
from api.services.music.spotify_data_service import SpotifyDataService, SpotifyDataServiceException


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
    A service for analyzing emotional analyses of top tracks.

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
    def _aggregate_emotions(emotional_analyses: list[EmotionalProfileResponse]) -> dict:
        """
        Aggregates emotional analysis results across multiple songs.

        This method sums up emotion percentages and tracks the song with the highest percentage for each emotion.

        Parameters
        ----------
        emotional_analyses : list[EmotionalProfileResponse]
            A list of `EmotionalProfile` objects containing emotional analysis results.

        Returns
        -------
        dict
            A dictionary where keys are emotion names, and values contain total emotion percentages and the track with
            the highest percentage for that emotion.
        """

        total_emotions = defaultdict(lambda: {"total": 0, "max_track": {"track_id": None, "percentage": 0}})

        for analysis in emotional_analyses:
            track_id = analysis.track_id
            emotional_profile = analysis.emotional_profile

            for emotion, percentage in emotional_profile.model_dump().items():
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
        KeyError
            If total_emotions dict does not contain the required keys.
        ZeroDivisionError
            If results_count == 0.
        pydantic.ValidationError
            If creating TopEmotion objects fails.
        """

        return [
            TopEmotion(
                name=emotion,
                percentage=round(info["total"] / result_count, 2),
                track_id=track_id
            )
            for emotion, info in total_emotions.items()
            if (track_id := info["max_track"]["track_id"]) is not None
        ]

    @staticmethod
    def _check_data_not_empty(data: list, label: str):
        """
        Checks if the provided data is empty and raises an exception if it is.

        Parameters
        ----------
        data : list
            The list of data to be checked.
        label : str
            A label representing the type of data being checked (e.g., "top tracks").

        Raises
        ------
        InsightsServiceException
            If the data list is empty, an exception is raised with an appropriate error message.
        """

        if len(data) == 0:
            error_message = f"No {label} found. Cannot proceed further with analysis."
            logger.error(error_message)
            raise InsightsServiceException(error_message)

    def _process_emotions(self, emotional_profiles: list[EmotionalProfileResponse], limit: int) -> list[TopEmotion]:
        """
        Processes the emotional profiles of the tracks and returns the top emotions.

        Parameters
        ----------
        emotional_profiles : list of EmotionalProfileResponse
            A list of `EmotionalProfileResponse` objects representing the emotional profiles of the tracks.
        limit : int
            The maximum number of top emotions to return.

        Returns
        -------
        list
            A list of `TopEmotion` objects representing the top emotions detected in the tracks, sorted by their
            average percentage.
        """

        total_emotions = self._aggregate_emotions(emotional_profiles)
        average_emotions = self._get_average_emotions(
            total_emotions=total_emotions,
            result_count=len(emotional_profiles)
        )
        top_emotions = sorted(average_emotions, key=lambda emotion: emotion.percentage, reverse=True)[:limit]
        return top_emotions

    async def get_top_emotions(self, time_range: TopItemTimeRange, limit: int = 5) -> list[TopEmotion]:
        """
        Retrieves the top emotions detected in a user's top Spotify tracks.

        This method fetches a user's top tracks from Spotify, retrieves lyrics for each track,
        performs emotional analysis, and returns the most prominent emotions.

        Parameters
        ----------
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
            top_items = await self.spotify_data_service.get_top_items(item_type=TopItemType.TRACK, time_range=time_range)
            self._check_data_not_empty(data=top_items, label="top tracks")
            top_tracks = [SpotifyTrack(**item.model_dump()) for item in top_items]

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
            self._check_data_not_empty(data=lyrics_list, label="lyrics")

            # get emotional profiles for each set of lyrics
            emotional_profile_requests = [
                EmotionalProfileRequest(
                    track_id=entry.track_id,
                    lyrics=entry.lyrics
                )
                for entry
                in lyrics_list
            ]
            emotional_profiles = await self.analysis_service.get_emotional_profiles(emotional_profile_requests)
            self._check_data_not_empty(data=emotional_profiles, label="emotional profiles")

            # get top emotions from all emotional profiles
            top_emotions = self._process_emotions(emotional_profiles=emotional_profiles, limit=limit)

            return top_emotions
        except (SpotifyDataServiceException, LyricsServiceException, AnalysisServiceException) as e:
            error_message = f"Service failure - {e}"
            logger.error(error_message)
            raise InsightsServiceException(error_message)
        except (pydantic.ValidationError, AttributeError) as e:
            error_message = f"Data validation failure - {e}"
            logger.error(error_message)
            raise InsightsServiceException(error_message)

    async def tag_lyrics_with_emotion(self, track_id: str, emotion: Emotion) -> EmotionalTagsResponse:
        """
        Retrieves emotional tags for a given track's lyrics based on the specified emotion.

        Parameters
        ----------
        track_id : str
            The ID of the track being analyzed.
        emotion : Emotion
            The emotion for which tagged lyrics are requested.

        Returns
        -------
        EmotionalTagsResponse
            A response object containing the emotional tags.

        Raises
        ------
        InsightsServiceException
            If any step of the retrieval process fails.
        """

        try:
            track_response = await self.spotify_data_service.get_item_by_id(item_id=track_id, item_type=TopItemType.TRACK)
            track = SpotifyTrack(**track_response.model_dump())

            lyrics_request = LyricsRequest(track_id=track.id, artist_name=track.artist.name, track_title=track.name)
            lyrics_response = await self.lyrics_service.get_lyrics(lyrics_request)

            emotional_tags_request = EmotionalTagsRequest(
                track_id=track_id,
                emotion=emotion,
                lyrics=lyrics_response.lyrics
            )
            emotional_tags_response = await self.analysis_service.get_emotional_tags(emotional_tags_request)

            return emotional_tags_response
        except (SpotifyDataServiceException, LyricsServiceException, AnalysisServiceException) as e:
            error_message = f"Service failure - {e}"
            logger.error(error_message)
            raise InsightsServiceException(error_message)
        except (pydantic.ValidationError, AttributeError) as e:
            error_message = f"Data validation failure - {e}"
            logger.error(error_message)
            raise InsightsServiceException(error_message)
