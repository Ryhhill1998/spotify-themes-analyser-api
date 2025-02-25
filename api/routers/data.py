from typing import Annotated

from fastapi import Depends, APIRouter
from fastapi.responses import JSONResponse
from httpx import HTTPStatusError

from api.dependencies import get_tokens_from_cookies, get_spotify_data_service, get_spotify_auth_service
from api.services.spotify_auth_service import SpotifyAuthService
from api.services.spotify_data_service import SpotifyDataService, TopItemType
from api.utils import set_response_cookie

router = APIRouter(prefix="/data")


@router.get("/top-tracks")
async def get_top_tracks(
        tokens: Annotated[tuple[str, str], Depends(get_tokens_from_cookies)],
        spotify_data_service: Annotated[SpotifyDataService, Depends(get_spotify_data_service)],
        spotify_auth_service: Annotated[SpotifyAuthService, Depends(get_spotify_auth_service)],
):
    access_token, refresh_token = tokens

    try:
        top_tracks = await spotify_data_service.get_top_items(access_token=access_token, item_type=TopItemType.TRACKS)
    except HTTPStatusError:
        refresh_data = await spotify_auth_service.refresh_access_token(refresh_token=refresh_token)
        access_token = refresh_data["access_token"]
        refresh_token = refresh_data["refresh_token"]
        top_tracks = await spotify_data_service.get_top_items(access_token=access_token, item_type=TopItemType.TRACKS)

    response = JSONResponse(content=top_tracks)
    set_response_cookie(response=response, key="access_token", value=access_token)
    set_response_cookie(response=response, key="refresh_token", value=refresh_token)

    return response
