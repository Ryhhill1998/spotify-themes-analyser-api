from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from loguru import logger

from api.dependencies import TokenCookieExtractionDependency, SpotifyDataServiceDependency, InsightsServiceDependency
from api.routers.utils import create_json_response_and_set_token_cookies, get_top_items_response
from api.services.insights_service import InsightsServiceException
from api.services.music.spotify_data_service import ItemType

router = APIRouter(prefix="/me")


@router.get("/top/artists")
async def get_top_artists(
        tokens: TokenCookieExtractionDependency,
        spotify_data_service: SpotifyDataServiceDependency
) -> JSONResponse:
    """
    Retrieves the user's top artists from Spotify.

    Parameters
    ----------
    tokens : TokenCookieExtractionDependency
        Dependency that extracts tokens from cookies.
    spotify_data_service : SpotifyDataServiceDependency
        Dependency for retrieving the user's top artists from the Spotify API.

    Returns
    -------
    JSONResponse
        A JSON response containing a list of top artists with updated token cookies.

    Raises
    ------
    HTTPException
        Raised with a 500 Internal Server Error status code if another exception occurs while retrieving the user's top
        artists from Spotify.
    """

    response = await get_top_items_response(
        spotify_data_service=spotify_data_service,
        tokens=tokens,
        item_type=ItemType.ARTISTS
    )

    return response


@router.get("/top/tracks")
async def get_top_tracks(
        tokens: TokenCookieExtractionDependency,
        spotify_data_service: SpotifyDataServiceDependency
) -> JSONResponse:
    """
    Retrieves the user's top tracks from Spotify.

    Parameters
    ----------
    tokens : TokenCookieExtractionDependency
        Dependency that extracts tokens from cookies.
    spotify_data_service : SpotifyDataServiceDependency
        Dependency for retrieving the user's top tracks from the Spotify API.

    Returns
    -------
    JSONResponse
        A JSON response containing a list of top tracks with updated token cookies.

    Raises
    ------
    HTTPException
        Raised with a 500 Internal Server Error status code if another exception occurs while retrieving the user's top
        tracks from Spotify.
    """

    response = await get_top_items_response(
        spotify_data_service=spotify_data_service,
        tokens=tokens,
        item_type=ItemType.TRACKS
    )

    return response


@router.get("/top/emotions")
async def get_top_emotions(
        tokens: TokenCookieExtractionDependency,
        insights_service: InsightsServiceDependency
) -> JSONResponse:
    """
    Retrieves the user's top emotional responses based on their music listening history.

    Parameters
    ----------
    tokens : TokenCookieExtractionDependency
        Dependency that extracts tokens from cookies.
    insights_service : InsightsServiceDependency
        Dependency for analyzing and retrieving the top emotions in the user's Spotify listening history.

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
        top_emotions_response = await insights_service.get_top_emotions(tokens)
        top_emotions = top_emotions_response.top_emotions
        tokens = top_emotions_response.tokens

        response_content = [emotion.model_dump() for emotion in top_emotions]
        response = create_json_response_and_set_token_cookies(content=response_content, tokens=tokens)

        return response
    except InsightsServiceException as e:
        error_message = "Failed to retrieve the user's top emotions"
        logger.exception(f"{error_message} - {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message)
