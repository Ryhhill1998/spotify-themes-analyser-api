from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from loguru import logger

from api.dependencies import AccessTokenDependency, SpotifyDataServiceDependency
from api.models import SpotifyArtist
from api.services.music.spotify_data_service import SpotifyDataServiceNotFoundException, SpotifyDataServiceException, \
    ItemType

router = APIRouter(prefix="/artists")


@router.get("/{artist_id}", response_model=SpotifyArtist)
async def get_artist_by_id(
        artist_id: str,
        access_token: AccessTokenDependency,
        spotify_data_service: SpotifyDataServiceDependency
) -> SpotifyArtist:
    """
    Retrieves details about a specific artist by their ID.

    Parameters
    ----------
    artist_id : str
        The Spotify artist ID.
    access_token : AccessTokenDependency
        Dependency that extracts access token from cookies.
    spotify_data_service : SpotifyDataServiceDependency
        Dependency for retrieving the artist data from the Spotify API.

    Returns
    -------
    JSONResponse
        A JSON response containing artist details with updated token cookies.

    Raises
    ------
    HTTPException
        Raised with a 404 Not Found status code if the requested Spotify artist was not found.
        Raised with a 500 Internal Server Error status code if another exception occurs while retrieving the requested
        artist from Spotify.
    """

    try:
        artist = await spotify_data_service.get_item_by_id(
            access_token=access_token,
            item_id=artist_id,
            item_type=ItemType.ARTISTS
        )
        return artist
    except SpotifyDataServiceNotFoundException as e:
        error_message = "Could not find the requested artist"
        logger.error(f"{error_message} - {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_message)
    except SpotifyDataServiceException as e:
        error_message = "Failed to retrieve the requested artist"
        logger.error(f"{error_message} - {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message)
