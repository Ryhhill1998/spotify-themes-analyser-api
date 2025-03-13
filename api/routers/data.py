from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from api.dependencies import TokenCookieExtractionDependency, SpotifyDataServiceDependency, InsightsServiceDependency
from api.models import TokenData
from api.services.insights_service import InsightsServiceException
from api.services.music.spotify_data_service import SpotifyDataService, ItemType, SpotifyDataServiceException, \
    SpotifyDataServiceNotFoundException
from api.utils import set_response_cookie

router = APIRouter(prefix="/data")


def create_json_response_and_set_token_cookies(content: list[dict] | dict, tokens: TokenData) -> JSONResponse:
    """
    Creates a JSON response and sets access and refresh tokens as cookies.

    Parameters
    ----------
    content : list[dict] | dict
        The JSON content to return in the response.
    tokens : TokenData
        The updated access and refresh tokens.

    Returns
    -------
    JSONResponse
        A JSON response containing the content with updated token cookies.
    """

    response = JSONResponse(content=content)
    set_response_cookie(response=response, key="access_token", value=tokens.access_token)
    set_response_cookie(response=response, key="refresh_token", value=tokens.refresh_token)

    return response


async def get_item_response(
        item_id: str,
        item_type: ItemType,
        tokens: TokenData,
        spotify_data_service: SpotifyDataService
) -> JSONResponse:
    """
    Retrieves information about a specific Spotify item (track or artist).

    Parameters
    ----------
    item_id : str
        The unique identifier of the item (track or artist).
    item_type : ItemType
        The type of item being retrieved (TRACKS or ARTISTS).
    tokens : TokenData
        The access and refresh tokens for authentication.
    spotify_data_service : SpotifyDataService
        The Spotify data service used to fetch the item details from the Spotify API.

    Returns
    -------
    JSONResponse
        A JSON response containing the item details with updated token cookies.

    Raises
    ------
    HTTPException
        Raised with a 404 Not Found status code if the requested Spotify item was not found.
        Raised with a 500 Internal Server Error status code if another exception occurs while retrieving the requested
        item from Spotify.
    """

    try:
        item_response = await spotify_data_service.get_item_by_id(item_id=item_id, tokens=tokens, item_type=item_type)
        tokens = item_response.tokens

        response_content = item_response.data.model_dump()
        response = create_json_response_and_set_token_cookies(content=response_content, tokens=tokens)

        return response
    except SpotifyDataServiceNotFoundException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Could not find the requested item.")
    except SpotifyDataServiceException:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong.")


@router.get("/artists/{artist_id}")
async def get_artist_by_id(
        artist_id: str,
        tokens: TokenCookieExtractionDependency,
        spotify_data_service: SpotifyDataServiceDependency
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
        spotify_data_service=spotify_data_service
    )

    return artist_response


@router.get("/tracks/{track_id}")
async def get_track_by_id(
        track_id: str,
        tokens: TokenCookieExtractionDependency,
        spotify_data_service: SpotifyDataServiceDependency
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
        spotify_data_service=spotify_data_service
    )

    return track_response


async def get_top_items_response(
        spotify_data_service: SpotifyDataService,
        tokens: TokenData,
        item_type: ItemType
) -> JSONResponse:
    """
    Retrieves a user's top items (tracks or artists) from Spotify.

    Parameters
    ----------
    spotify_data_service : SpotifyDataService
        The Spotify data service used to fetch the top items from the Spotify API.
    tokens : TokenData
        The access and refresh tokens for authentication.
    item_type : ItemType
        The type of items to retrieve (TRACKS or ARTISTS).

    Returns
    -------
    JSONResponse
        A JSON response containing a list of top items with updated token cookies.

    Raises
    ------
    HTTPException
        Raised with a 500 Internal Server Error status code if another exception occurs while retrieving the requested
        data from Spotify.
    """

    try:
        top_items_response = await spotify_data_service.get_top_items(
            tokens=tokens,
            item_type=item_type
        )
        tokens = top_items_response.tokens

        response_content = [item.model_dump() for item in top_items_response.data]
        response = create_json_response_and_set_token_cookies(content=response_content, tokens=tokens)

        return response
    except SpotifyDataServiceException:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong.")


@router.get("/top-artists")
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


@router.get("/top-tracks")
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


@router.get("/top-emotions")
async def get_top_emotions(
        tokens: TokenCookieExtractionDependency,
        insights_service: InsightsServiceDependency,
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
    except InsightsServiceException:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong.")
