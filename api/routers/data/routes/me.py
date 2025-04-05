from typing import Annotated

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import Field

from api.dependencies import AccessTokenDependency, SpotifyDataServiceDependency, InsightsServiceDependency
from api.models import SpotifyArtist, SpotifyProfile
from api.services.insights_service import InsightsServiceException
from api.services.music.spotify_data_service import ItemType, TimeRange, SpotifyDataServiceException, \
    SpotifyDataServiceUnauthorisedException

router = APIRouter(prefix="/me")


@router.get("/profile", response_model=SpotifyProfile)
async def get_profile(
        spotify_data_service: SpotifyDataServiceDependency
) -> SpotifyProfile:
    try:
        profile_data = await spotify_data_service.get_profile_data()
        return profile_data
    except SpotifyDataServiceUnauthorisedException as e:
        error_message = "Invalid access token"
        logger.error(f"{error_message} - {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=error_message)



@router.get("/top/artists", response_model=list[SpotifyArtist])
async def get_top_artists(
        spotify_data_service: SpotifyDataServiceDependency,
        time_range: TimeRange,
        limit: Annotated[int, Field(ge=10, le=50)] = 50
) -> list[SpotifyArtist]:
    """
    Retrieves the user's top artists from Spotify.

    Parameters
    ----------
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

    try:
        top_artists = await spotify_data_service.get_top_items(
            item_type=ItemType.ARTISTS,
            time_range=time_range.value,
            limit=limit
        )
        return top_artists
    except SpotifyDataServiceUnauthorisedException as e:
        error_message = "Invalid access token"
        logger.error(f"{error_message} - {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=error_message)
    except SpotifyDataServiceException as e:
        error_message = "Failed to retrieve the user's top artists"
        logger.error(f"{error_message} - {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message)


@router.get("/top/tracks")
async def get_top_tracks(
        spotify_data_service: SpotifyDataServiceDependency,
        time_range: TimeRange,
        limit: Annotated[int, Field(ge=10, le=50)] = 50
) -> JSONResponse:
    """
    Retrieves the user's top tracks from Spotify.

    Parameters
    ----------
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

    try:
        top_tracks = await spotify_data_service.get_top_items(
            item_type=ItemType.TRACKS,
            time_range=time_range.value,
            limit=limit
        )
        return top_tracks
    except SpotifyDataServiceUnauthorisedException as e:
        error_message = "Invalid access token"
        logger.error(f"{error_message} - {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=error_message)
    except SpotifyDataServiceException as e:
        error_message = "Failed to retrieve the user's top tracks"
        logger.error(f"{error_message} - {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message)


@router.get("/top/emotions")
async def get_top_emotions(
        insights_service: InsightsServiceDependency,
        time_range: TimeRange
) -> JSONResponse:
    """
    Retrieves the user's top emotional responses based on their music listening history.

    Parameters
    ----------
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
        top_emotions = await insights_service.get_top_emotions(time_range.value)
        return top_emotions
    except InsightsServiceException as e:
        error_message = "Failed to retrieve the user's top emotions"
        logger.error(f"{error_message} - {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message)
