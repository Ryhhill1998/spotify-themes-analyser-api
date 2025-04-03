from typing import Annotated

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import Field

from api.dependencies import TokenCookieExtractionDependency, SpotifyDataServiceDependency, InsightsServiceDependency, \
    SettingsDependency
from api.routers.utils import create_json_response_and_set_token_cookies, get_top_items_response
from api.services.insights_service import InsightsServiceException
from api.services.music.spotify_data_service import ItemType, TimeRange

router = APIRouter(prefix="/me")


@router.get("/profile")
async def get_profile(
        tokens: TokenCookieExtractionDependency,
        spotify_data_service: SpotifyDataServiceDependency,
        settings: SettingsDependency
) -> JSONResponse:
    profile_data = await spotify_data_service.get_profile_data(tokens)
    tokens = profile_data.tokens

    response_content = profile_data.profile.model_dump()
    response = create_json_response_and_set_token_cookies(content=response_content, tokens=tokens, domain=settings.domain)

    return response


@router.get("/top/artists")
async def get_top_artists(
        tokens: TokenCookieExtractionDependency,
        spotify_data_service: SpotifyDataServiceDependency,
        settings: SettingsDependency,
        time_range: TimeRange,
        limit: Annotated[int, Field(ge=10, le=50)] = 50
) -> JSONResponse:
    """
    Retrieves the user's top artists from Spotify.

    Parameters
    ----------
    tokens : TokenCookieExtractionDependency
        Dependency that extracts tokens from cookies.
    spotify_data_service : SpotifyDataServiceDependency
        Dependency for retrieving the user's top artists from the Spotify API.
    limit : int
        Limit to specify the number of top artists to retrieve (default is 50, must be at least 10 but no more than 50).

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
        domain=settings.domain,
        tokens=tokens,
        item_type=ItemType.ARTISTS,
        time_range=time_range,
        limit=limit
    )

    return response


@router.get("/top/tracks")
async def get_top_tracks(
        tokens: TokenCookieExtractionDependency,
        spotify_data_service: SpotifyDataServiceDependency,
        settings: SettingsDependency,
        time_range: TimeRange,
        limit: Annotated[int, Field(ge=10, le=50)] = 50
) -> JSONResponse:
    """
    Retrieves the user's top tracks from Spotify.

    Parameters
    ----------
    tokens : TokenCookieExtractionDependency
        Dependency that extracts tokens from cookies.
    spotify_data_service : SpotifyDataServiceDependency
        Dependency for retrieving the user's top tracks from the Spotify API.
    limit : int
        Limit to specify the number of top tracks to retrieve (default is 50, must be at least 10 but no more than 50).

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
        domain=settings.domain,
        tokens=tokens,
        item_type=ItemType.TRACKS,
        time_range=time_range,
        limit=limit
    )

    return response


@router.get("/top/emotions")
async def get_top_emotions(
        tokens: TokenCookieExtractionDependency,
        insights_service: InsightsServiceDependency,
        settings: SettingsDependency,
        time_range: TimeRange
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
        top_emotions_response = await insights_service.get_top_emotions(tokens=tokens, time_range=time_range)
        top_emotions = top_emotions_response.top_emotions
        tokens = top_emotions_response.tokens

        response_content = [emotion.model_dump() for emotion in top_emotions]
        response = create_json_response_and_set_token_cookies(content=response_content, tokens=tokens, domain=settings.domain)

        return response
    except InsightsServiceException as e:
        error_message = "Failed to retrieve the user's top emotions"
        logger.exception(f"{error_message} - {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message)
