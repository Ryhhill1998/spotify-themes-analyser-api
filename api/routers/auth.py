import secrets
import urllib.parse
from typing import Annotated
from requests.exceptions import HTTPError

from fastapi import Response, Depends, Request
from fastapi.responses import RedirectResponse

from api.dependencies import get_settings, get_spotify_auth_service
from fastapi import APIRouter

from api.services.spotify_auth_service import SpotifyAuthService
from api.settings import Settings
from api.utils import set_response_cookie

router = APIRouter(prefix="/auth")


def create_custom_redirect_response(redirect_url: str) -> Response:
    return Response(headers={"location": redirect_url}, status_code=307)


def generate_state() -> str:
    return secrets.token_hex(16)


def validate_state(stored_state: str, received_state: str):
    if stored_state != received_state:
        raise ValueError("Received state does not match stored state.")


@router.get("/spotify/login")
async def login(spotify_auth_service: Annotated[SpotifyAuthService, Depends(get_spotify_auth_service)]):
    state = generate_state()
    url = spotify_auth_service.generate_auth_url(state)

    response = create_custom_redirect_response(url)
    set_response_cookie(response=response, key="oauth_state", value=state)

    return response


@router.get("/spotify/callback")
async def callback(
        code: str,
        state: str,
        request: Request,
        spotify_auth_service: Annotated[SpotifyAuthService, Depends(get_spotify_auth_service)],
        settings: Annotated[Settings, Depends(get_settings)],
):
    try:
        # make sure that state stored in login route is same as that received after authenticating
        # prevents csrf
        validate_state(stored_state=request.cookies["oauth_state"], received_state=state)

        # get access and refresh tokens from spotify API to allow future API calls on behalf of the user
        tokens = await spotify_auth_service.get_tokens_with_auth_code(code)

        response = create_custom_redirect_response(settings.frontend_url)
        set_response_cookie(response=response, key="access_token", value=tokens["access_token"])
        set_response_cookie(response=response, key="refresh_token", value=tokens["refresh_token"])

        return response
    except (HTTPError, ValueError):
        error_params = urllib.parse.urlencode({"error": "authentication-failure"})
        return RedirectResponse(f"{settings.frontend_url}/#{error_params}")
