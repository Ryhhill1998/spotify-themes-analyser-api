import secrets
import urllib.parse
from typing import Annotated

import requests
from fastapi import Response, Depends
from fastapi.responses import RedirectResponse

from api.dependencies import get_auth_header, get_settings
from fastapi import APIRouter

from api.settings import Settings
from api.utils import set_response_cookie

router = APIRouter(prefix="/auth")


@router.get("/spotify/login")
async def login(response: Response, settings: Annotated[Settings, Depends(get_settings)]):
    state = secrets.token_hex(16)
    scope = settings.spotify_auth_user_scopes
    response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        secure=True,
        samesite="lax"
    )

    params = {
        "client_id": settings.spotify_client_id,
        "response_type": "code",
        "redirect_uri": settings.spotify_auth_redirect_uri,
        "scope": scope,
        "state": state
    }
    url = f"{settings.spotify_auth_base_url}/authorize?" + urllib.parse.urlencode(params)
    print(params)
    print(url)

    return RedirectResponse(url)


@router.get("/spotify/callback")
async def callback(
        code: Annotated[str, None],
        state: Annotated[str, None],
        auth_header: Annotated[str, Depends(get_auth_header)],
        settings: Annotated[Settings, Depends(get_settings)],
):
    token_response = requests.post(
        url=f"{settings.spotify_auth_base_url}/api/token",
        headers={
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded"
        },
        data={
            "code": code,
            "redirect_uri": settings.spotify_auth_redirect_uri,
            "grant_type": "authorization_code"
        }
    )

    if token_response.status_code != 200:
        error_params = urllib.parse.urlencode({"error": "invalid_token"})
        return RedirectResponse(f"{settings.frontend_url}/#{error_params}")

    token_data = token_response.json()
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")

    response = Response(headers={"location": settings.frontend_url}, status_code=307)
    set_response_cookie(response=response, key="access_token", value=access_token)
    set_response_cookie(response=response, key="refresh_token", value=refresh_token)

    return response
