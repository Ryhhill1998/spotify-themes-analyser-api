from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from loguru import logger

from api.dependencies import TokenCookieExtractionDependency, SpotifyDataServiceDependency, InsightsServiceDependency, \
    SettingsDependency
from api.models import Emotion
from api.routers.utils import get_item_response, create_json_response_and_set_token_cookies
from api.services.insights_service import InsightsServiceException
from api.services.music.spotify_data_service import ItemType

router = APIRouter(prefix="/tracks")


@router.get("/{track_id}")
async def get_track_by_id(
        track_id: str,
        tokens: TokenCookieExtractionDependency,
        spotify_data_service: SpotifyDataServiceDependency,
        settings: SettingsDependency
) -> JSONResponse:
    """
    Retrieves details about a specific track by its ID.

    Parameters
    ----------
    track_id : str
        The Spotify track ID.
    tokens : TokenCookieExtractionDependency
        Dependency that extracts tokens from cookies.
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

    track_response = await get_item_response(
        item_id=track_id,
        item_type=ItemType.TRACKS,
        tokens=tokens,
        spotify_data_service=spotify_data_service,
        domain=settings.domain
    )

    return track_response


@router.get("/{track_id}/lyrics/emotional-tags/{emotion}")
async def get_lyrics_tagged_with_emotion(
        track_id: str,
        emotion: Emotion,
        tokens: TokenCookieExtractionDependency,
        insights_service: InsightsServiceDependency,
        settings: SettingsDependency
) -> JSONResponse:
    """
    Retrieves the user's top emotional responses based on their music listening history.

    Parameters
    ----------
    track_id : str
        The ID of the track being requested.
    tokens : TokenCookieExtractionDependency
        Dependency that extracts tokens from cookies.
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
        tagged_lyrics_response = await insights_service.tag_lyrics_with_emotion(
            track_id=track_id,
            emotion=emotion,
            tokens=tokens
        )

        response_content = tagged_lyrics_response.lyrics_data.model_dump()
        response = create_json_response_and_set_token_cookies(
            content=response_content,
            tokens=tagged_lyrics_response.tokens,
            domain=settings.domain
        )

        return response
    except InsightsServiceException as e:
        error_message = "Failed to tag lyrics with requested emotion"
        logger.exception(f"{error_message} - {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message)
