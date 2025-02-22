import secrets
import urllib.parse
from typing import Annotated
from requests.exceptions import HTTPError

from fastapi import Response, Depends
from fastapi.responses import RedirectResponse

from api.dependencies import get_settings, get_spotify_auth_service
from fastapi import APIRouter

from api.services.spotify_auth_service import SpotifyAuthService
from api.settings import Settings
from api.utils import set_response_cookie

router = APIRouter(prefix="/auth")


@router.get("/spotify/login")
async def login(spotify_auth_service: Annotated[SpotifyAuthService, Depends(get_spotify_auth_service)]):
    state = secrets.token_hex(16)
    url = spotify_auth_service.generate_auth_url(state)

    response = Response(headers={"location": url}, status_code=307)
    set_response_cookie(response=response, key="oauth_state", value=state)

    return response


@router.get("/spotify/callback")
async def callback(
        code: str,
        state: str,
        spotify_auth_service: Annotated[SpotifyAuthService, Depends(get_spotify_auth_service)],
        settings: Annotated[Settings, Depends(get_settings)],
):
    try:
        tokens = spotify_auth_service.get_tokens_with_auth_code(code)
    except HTTPError:
        error_params = urllib.parse.urlencode({"error": "invalid-token"})
        return RedirectResponse(f"{settings.frontend_url}/#{error_params}")

    response = Response(headers={"location": settings.frontend_url}, status_code=307)
    set_response_cookie(response=response, key="access_token", value=tokens["access_token"])
    set_response_cookie(response=response, key="refresh_token", value=tokens["refresh_token"])

    return response
