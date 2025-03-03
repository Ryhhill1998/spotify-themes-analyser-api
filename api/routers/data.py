from typing import Annotated

from fastapi import Depends, APIRouter
from fastapi.responses import JSONResponse

from api.dependencies import get_tokens_from_cookies, get_spotify_data_service, get_spotify_auth_service, \
    get_lyrics_service
from api.models import LyricsRequest, LyricsResponse
from api.services.lyrics_service import LyricsService
from api.services.spotify.spotify_auth_service import SpotifyAuthService
from api.services.spotify.spotify_data_service import SpotifyDataService, TopItemType
from api.utils import set_response_cookie

router = APIRouter(prefix="/data")

# initialise dependencies
token_cookie_extraction_dependency = Annotated[tuple[str, str], Depends(get_tokens_from_cookies)]
spotify_auth_service_dependency = Annotated[SpotifyAuthService, Depends(get_spotify_auth_service)]
spotify_data_service_dependency = Annotated[SpotifyDataService, Depends(get_spotify_data_service)]
lyrics_service_dependency = Annotated[LyricsService, Depends(get_lyrics_service)]


async def get_top_items_response(
        spotify_data_service: SpotifyDataService,
        access_token: str,
        refresh_token: str,
        item_type: TopItemType
) -> JSONResponse:
    top_items_response = await spotify_data_service.get_top_items(
        access_token=access_token,
        refresh_token=refresh_token,
        item_type=item_type
    )

    response_content = [item.model_dump() for item in top_items_response.data]

    response = JSONResponse(content=response_content)
    set_response_cookie(response=response, key="access_token", value=top_items_response.access_token)
    set_response_cookie(response=response, key="refresh_token", value=top_items_response.refresh_token)

    return response


@router.get("/top-artists")
async def get_top_artists(
        tokens: token_cookie_extraction_dependency,
        spotify_data_service: spotify_data_service_dependency
) -> JSONResponse:
    access_token, refresh_token = tokens

    response = await get_top_items_response(
        spotify_data_service=spotify_data_service,
        access_token=access_token,
        refresh_token=refresh_token,
        item_type=TopItemType.ARTISTS
    )

    return response


@router.get("/top-tracks")
async def get_top_tracks(
        tokens: token_cookie_extraction_dependency,
        spotify_data_service: spotify_data_service_dependency
) -> JSONResponse:
    access_token, refresh_token = tokens

    response = await get_top_items_response(
        spotify_data_service=spotify_data_service,
        access_token=access_token,
        refresh_token=refresh_token,
        item_type=TopItemType.TRACKS
    )

    return response


@router.post("/lyrics-list")
async def retrieve_lyrics_list(
        lyrics_requests: list[LyricsRequest],
        lyrics_service: lyrics_service_dependency
) -> list[LyricsResponse]:
    lyrics_list = await lyrics_service.get_lyrics_list(lyrics_requests)

    return lyrics_list
