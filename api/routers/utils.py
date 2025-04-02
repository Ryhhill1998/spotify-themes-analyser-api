from fastapi import Response, HTTPException, status
from fastapi.responses import JSONResponse
from loguru import logger

from api.models import TokenData
from api.services.music.spotify_data_service import SpotifyDataServiceNotFoundException, SpotifyDataServiceException, \
    SpotifyDataService, ItemType, TimeRange


def set_response_cookie(response: Response, key: str, value: str):
    # must rememeber to set secure=True before production
    response.set_cookie(key=key, value=value, httponly=True, secure=False, samesite="lax")


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
    except SpotifyDataServiceNotFoundException as e:
        error_message = "Could not find the requested item"
        logger.exception(f"{error_message} - {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_message)
    except SpotifyDataServiceException as e:
        error_message = "Failed to retrieve the requested item"
        logger.exception(f"{error_message} - {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message)


async def get_top_items_response(
        spotify_data_service: SpotifyDataService,
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
        response = create_json_response_and_set_token_cookies(content=response_content, tokens=tokens)

        return response
    except SpotifyDataServiceException as e:
        error_message = "Failed to retrieve the user's top items"
        logger.exception(f"{error_message} - {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message)
