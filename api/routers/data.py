from typing import Annotated

from fastapi import Depends, APIRouter
from fastapi.responses import JSONResponse
from httpx import HTTPStatusError
from pydantic import BaseModel

from api.dependencies import get_tokens_from_cookies, get_spotify_data_service, get_spotify_auth_service, \
    get_lyrics_service
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


@router.get("/top-tracks")
async def get_top_tracks(
        tokens: token_cookie_extraction_dependency,
        spotify_data_service: spotify_data_service_dependency,
        spotify_auth_service: spotify_auth_service_dependency,
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


class LyricsRequest(BaseModel):
    artist: str
    track_title: str


class LyricsResponse(LyricsRequest):
    lyrics: str


@router.post("/lyrics")
async def retrieve_lyrics(
        track_requested: LyricsRequest,
        lyrics_service: lyrics_service_dependency
) -> LyricsResponse:
    data = await lyrics_service.get_lyrics(track_requested.dict())

    return LyricsResponse(**data)


@router.post("/lyrics-list")
async def retrieve_lyrics_list(
        tracks_requested: list[LyricsRequest],
        lyrics_service: lyrics_service_dependency
) -> list[LyricsResponse]:
    data = await lyrics_service.get_lyrics_list([track_req.dict() for track_req in tracks_requested])

    return [LyricsResponse(**entry) for entry in data]
