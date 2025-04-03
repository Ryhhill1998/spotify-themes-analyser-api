from fastapi import Response, HTTPException, status
from fastapi.responses import JSONResponse
from loguru import logger

from api.models import TokenData
from api.services.music.spotify_data_service import SpotifyDataServiceNotFoundException, SpotifyDataServiceException, \
    SpotifyDataService, ItemType, TimeRange


def set_response_cookie(response: Response, key: str, value: str):
    response.set_cookie(key=key, value=value, httponly=True, secure=True, samesite="none")


async def get_top_items_response(
        spotify_data_service: SpotifyDataService,
        domain: str,
        tokens: TokenData,
        item_type: ItemType,
        time_range: TimeRange,
        limit: int
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
    limit : int
        Limit to specify the number of top items to retrieve.

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
            item_type=item_type,
            time_range=time_range,
            limit=limit
        )
        tokens = top_items_response.tokens

        response_content = [item.model_dump() for item in top_items_response.data]
        response = create_json_response_and_set_token_cookies(content=response_content, tokens=tokens, domain=domain)

        return response
    except SpotifyDataServiceException as e:
        error_message = "Failed to retrieve the user's top items"
        logger.error(f"{error_message} - {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message)
