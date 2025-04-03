from fastapi import APIRouter
from fastapi.responses import JSONResponse

from api.dependencies import TokenCookieExtractionDependency, SpotifyDataServiceDependency, SettingsDependency
from api.routers.utils import get_item_response
from api.services.music.spotify_data_service import ItemType

router = APIRouter(prefix="/artists")


@router.get("/{artist_id}")
async def get_artist_by_id(
        artist_id: str,
        tokens: TokenCookieExtractionDependency,
        spotify_data_service: SpotifyDataServiceDependency,
        settings: SettingsDependency
) -> JSONResponse:
    """
    Retrieves details about a specific artist by their ID.

    Parameters
    ----------
    artist_id : str
        The Spotify artist ID.
    tokens : TokenCookieExtractionDependency
        Dependency that extracts tokens from cookies.
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

    artist_response = await get_item_response(
        item_id=artist_id,
        item_type=ItemType.ARTISTS,
        tokens=tokens,
        spotify_data_service=spotify_data_service,
        domain=settings.domain
    )

    return artist_response
