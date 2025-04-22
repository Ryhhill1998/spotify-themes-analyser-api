from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from loguru import logger

from api.data_structures.enums import TopItemType
from api.dependencies import SpotifyDataServiceDependency, InsightsServiceDependency
from api.data_structures.models import Emotion, EmotionalTagsResponse, SpotifyTrack
from api.services.insights_service import InsightsServiceException
from api.services.music.spotify_data_service import SpotifyDataServiceNotFoundException, SpotifyDataServiceException

router = APIRouter(prefix="/tracks")


@router.get("/{track_id}", response_model=SpotifyTrack)
async def get_track_by_id(track_id: str, spotify_data_service: SpotifyDataServiceDependency) -> SpotifyTrack:
    """
    Retrieves details about a specific track by its ID.

    Parameters
    ----------
    track_id : str
        The Spotify track ID.
    spotify_data_service : SpotifyDataServiceDependency
        Dependency for retrieving the track data from the Spotify API.

    Returns
    -------
    JSONResponse
        A JSON response containing track details with updated token cookies.

    Raises
    ------
    HTTPException
        Raised with a 404 Not Found status code if the requested Spotify track was not found.
        Raised with a 500 Internal Server Error status code if another exception occurs while retrieving the requested
        track from Spotify.
    """

    try:
        track = await spotify_data_service.get_item_by_id(item_id=track_id, item_type=TopItemType.TRACK)
        return track
    except SpotifyDataServiceNotFoundException as e:
        error_message = "Could not find the requested track"
        logger.error(f"{error_message} - {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_message)
    except SpotifyDataServiceException as e:
        error_message = "Failed to retrieve the requested track"
        logger.error(f"{error_message} - {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message)


@router.get("/{track_id}/lyrics/emotional-tags/{emotion}", response_model=EmotionalTagsResponse)
async def get_lyrics_tagged_with_emotion(
        track_id: str,
        emotion: Emotion,
        insights_service: InsightsServiceDependency
) -> EmotionalTagsResponse:
    """
    Retrieves the user's top emotional responses based on their music listening history.

    Parameters
    ----------
    track_id : str
        The ID of the track being requested.
    emotion : Emotion
        The emotion requested to tag the lyrics with.
    insights_service : InsightsServiceDependency
        Dependency for generating lyrics tagged with the requested emotion.

    Returns
    -------
    JSONResponse
        A JSON response containing a list of top emotional responses with updated token cookies.

    Raises
    ------
    HTTPException
        Raised with a 500 Internal Server Error status code if an exception occurs while computing the user's top
        emotions.
    """

    try:
        tagged_lyrics_response = await insights_service.tag_lyrics_with_emotion(track_id=track_id, emotion=emotion)
        return tagged_lyrics_response
    except InsightsServiceException as e:
        error_message = "Failed to tag lyrics with requested emotion"
        logger.error(f"{error_message} - {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message)
