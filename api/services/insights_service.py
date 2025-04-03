from collections import defaultdict

import pydantic
from loguru import logger

from api.models import TokenData, LyricsRequest, TopEmotionsResponse, TopEmotion, EmotionalProfileResponse, \
    EmotionalProfileRequest, EmotionalTagsRequest, Emotion, TaggedLyricsResponse, SpotifyTrack, LyricsResponse, \
    EmotionalTagsResponse
from api.services.analysis_service import AnalysisService, AnalysisServiceException
from api.services.lyrics_service import LyricsService, LyricsServiceException
from api.services.music.spotify_data_service import SpotifyDataService, ItemType, SpotifyDataServiceException, TimeRange


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

    async def _fetch_top_tracks(self, tokens: TokenData, time_range: TimeRange) -> tuple[list[SpotifyTrack], TokenData]:
        """
        Fetches the user's top tracks from Spotify.

        Parameters
        ----------
        tokens : TokenData
            The authentication tokens to be used for the request.

        Returns
        -------
        tuple
            A tuple containing:
            - A list of `SpotifyTrack` objects representing the top tracks.
            - The updated `TokenData` containing new tokens.

        Raises
        ------
        InsightsServiceException
            If no top tracks are found, an exception is raised.
        """

        top_tracks_response = await self.spotify_data_service.get_top_items(
            tokens=tokens,
            item_type=ItemType.TRACKS,
            time_range=time_range
        )
        top_tracks = [SpotifyTrack(**item.model_dump()) for item in top_tracks_response.data]
        self._check_data_not_empty(data=top_tracks, label="top tracks")
        tokens = top_tracks_response.tokens
        return top_tracks, tokens

    async def _fetch_lyrics_list(self, top_tracks: list[SpotifyTrack]) -> list[LyricsResponse]:
        """
        Fetches the lyrics for a list of top tracks.

        Parameters
        ----------
        top_tracks : list of SpotifyTrack
            A list of Spotify tracks for which lyrics need to be fetched.

        Returns
        -------
        list
            A list of `LyricsResponse` objects containing the lyrics for each track.

        Raises
        ------
        InsightsServiceException
            If no lyrics are found, an exception is raised.
        """

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
        return lyrics_list

    async def _analyse_emotions(self, lyrics_list: list[LyricsResponse]):
        """
        Analyzes the emotions detected in the lyrics of the provided tracks.

        Parameters
        ----------
        lyrics_list : list of LyricsResponse
            A list of `LyricsResponse` objects containing lyrics for each track.

        Returns
        -------
        list
            A list of `EmotionalProfileResponse` objects representing the emotional profiles of the tracks.

        Raises
        ------
        InsightsServiceException
            If no emotional profiles are found, an exception is raised.
        """

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
        return emotional_profiles

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

    async def get_top_emotions(self, tokens: TokenData, time_range: TimeRange, limit: int = 5) -> TopEmotionsResponse:
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
            top_tracks, tokens = await self._fetch_top_tracks(tokens=tokens, time_range=time_range)

            # get lyrics for each track
            lyrics_list = await self._fetch_lyrics_list(top_tracks)

            # get emotional profiles for each set of lyrics
            emotional_profiles = await self._analyse_emotions(lyrics_list)

            # get top emotions from all emotional profiles
            top_emotions = self._process_emotions(emotional_profiles=emotional_profiles, limit=limit)

            # convert top emotions and tokens to top emotions response object and return
            return TopEmotionsResponse(top_emotions=top_emotions, tokens=tokens)
        except (SpotifyDataServiceException, LyricsServiceException, AnalysisServiceException) as e:
            error_message = f"Service failure - {e}"
            logger.error(error_message)
            raise InsightsServiceException(error_message)
        except (pydantic.ValidationError, AttributeError) as e:
            error_message = f"Data validation failure - {e}"
            logger.error(error_message)
            raise InsightsServiceException(error_message)

    async def _fetch_track_details(self, track_id: str, tokens: TokenData) -> tuple[SpotifyTrack, TokenData]:
        """
        Fetches the details of a specific track by its ID.

        Parameters
        ----------
        track_id : str
            The unique identifier of the track whose details are to be fetched.
        tokens : TokenData
            The authentication tokens used for the request.

        Returns
        -------
        tuple
            A tuple containing:
            - A `SpotifyTrack` object representing the track's details.
            - The updated `TokenData` containing new tokens.

        Raises
        ------
        InsightsServiceException
            If the track details cannot be fetched, an exception is raised.
        """

        track_response = await self.spotify_data_service.get_item_by_id(
            item_id=track_id,
            tokens=tokens,
            item_type=ItemType.TRACKS
        )
        track = SpotifyTrack(**track_response.data.model_dump())
        tokens = track_response.tokens
        return track, tokens

    async def _fetch_lyrics(self, track: SpotifyTrack) -> LyricsResponse:
        """
        Fetches the lyrics for a given track.

        Parameters
        ----------
        track : SpotifyTrack
            The track for which lyrics need to be fetched.

        Returns
        -------
        LyricsResponse
            A `LyricsResponse` object containing the lyrics of the track.

        Raises
        ------
        InsightsServiceException
            If the lyrics cannot be fetched, an exception is raised.
        """

        lyrics_request = LyricsRequest(track_id=track.id, artist_name=track.artist.name, track_title=track.name)
        return await self.lyrics_service.get_lyrics(lyrics_request)

    async def _fetch_emotional_tags(self, track_id: str, emotion: Emotion, lyrics: str) -> EmotionalTagsResponse:
        """
        Fetches emotional tags for a given track's lyrics based on a specific emotion.

        Parameters
        ----------
        track_id : str
            The unique identifier of the track whose emotional tags are to be fetched.
        emotion : Emotion
            The specific emotion to be detected in the track's lyrics (e.g., "joy", "anger").
        lyrics : str
            The lyrics of the track to be analyzed for emotional content.

        Returns
        -------
        EmotionalTagsResponse
            An `EmotionalTagsResponse` object containing the detected emotional tags for the track's lyrics.

        Raises
        ------
        InsightsServiceException
            If the emotional tags cannot be fetched, an exception is raised.
        """

        emotional_tags_request = EmotionalTagsRequest(track_id=track_id, emotion=emotion, lyrics=lyrics)
        return await self.analysis_service.get_emotional_tags(emotional_tags_request)

    async def tag_lyrics_with_emotion(
            self,
            track_id: str,
            emotion: Emotion,
            tokens: TokenData
    ) -> TaggedLyricsResponse:
        """
        Retrieves emotional tags for a given track's lyrics based on the specified emotion.

        Parameters
        ----------
        track_id : str
            The ID of the track being analyzed.
        emotion : Emotion
            The emotion for which tagged lyrics are requested.
        tokens : TokenData
            The authentication tokens required for API access.

        Returns
        -------
        EmotionalTagsResponse
            A response object containing the emotional tags and updated tokens.

        Raises
        ------
        InsightsServiceException
            If any step of the retrieval process fails.
        """

        try:
            track, tokens = await self._fetch_track_details(track_id, tokens)
            lyrics_response = await self._fetch_lyrics(track)
            emotional_tags_response = await self._fetch_emotional_tags(track_id, emotion, lyrics_response.lyrics)

            return TaggedLyricsResponse(lyrics_data=emotional_tags_response, tokens=tokens)
        except (SpotifyDataServiceException, LyricsServiceException, AnalysisServiceException) as e:
            error_message = f"Service failure - {e}"
            logger.error(error_message)
            raise InsightsServiceException(error_message)
        except (pydantic.ValidationError, AttributeError) as e:
            error_message = f"Data validation failure - {e}"
            logger.error(error_message)
            raise InsightsServiceException(error_message)
