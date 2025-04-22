from datetime import datetime, timezone, timedelta
from typing import Annotated

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import Field
import pandas as pd

from api.dependencies import AccessTokenDependency, SpotifyDataServiceDependency, InsightsServiceDependency, \
    DBServiceDependency
from api.models import SpotifyArtist, SpotifyProfile
from api.services.db_service import DBServiceException
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



@router.get("/top/artists")
async def get_top_artists(
        user_id: str,
        spotify_data_service: SpotifyDataServiceDependency,
        db_service: DBServiceDependency,
        time_range: TimeRange,
        limit: Annotated[int, Field(ge=10, le=50)] = 50
):
    """
    Retrieves the user's top artists from Spotify.

    Parameters
    ----------
    user_id : str
        The spotify user ID of the signed in user.
    spotify_data_service : SpotifyDataServiceDependency
        Dependency for retrieving the user's top artists from the Spotify API.
    db_service : DBServiceDependency
        Dependency for retrieving the user's top artists from the database.
    time_range : TimeRange
        The time range to retrieve the top artists for.
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
        try:
            top_artists_db = db_service.get_top_artists(user_id=user_id, time_range=time_range)

            if not top_artists_db:
                top_artists = spotify_data_service.get_top_items(
                    item_type=ItemType.ARTISTS,
                    time_range=time_range,
                    limit=limit
                )
                return top_artists

            # get spotify artist objects
            ids = list(map(lambda db_artist: db_artist["artist_id"], top_artists_db))
            spotify_top_artists = await spotify_data_service.get_many_items_by_ids(item_ids=ids, item_type=ItemType.ARTISTS)
            artist_id_to_top_artist_map = {artist.id: artist for artist in spotify_top_artists}

            # combine records with artist data from spotify
            top_artists = []

            for db_artist in top_artists_db:
                artist_id = db_artist["artist_id"]
                artist_position_change = db_artist["position_change"]
                artist_is_new = db_artist["is_new"]

                artist = artist_id_to_top_artist_map[artist_id]

                if artist_is_new:
                    artist.position_change = "new"
                else:
                    artist.position_change = artist_position_change

                top_artists.append(artist)

            return top_artists
        except DBServiceException as e:
            error_message = "Failed to retrieve the user's top artists from the db"
            logger.error(f"{error_message} - {e}")

            top_artists = spotify_data_service.get_top_items(
                item_type=ItemType.ARTISTS,
                time_range=time_range,
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
