import secrets
import urllib.parse
from typing import Annotated

from fastapi import Response, APIRouter, Request, Body, HTTPException
from fastapi.responses import RedirectResponse
from loguru import logger

from api.dependencies import SpotifyAuthServiceDependency, SettingsDependency
from api.models import TokenData
from api.services.music.spotify_auth_service import SpotifyAuthServiceException

router = APIRouter(prefix="/spotify")


def create_custom_redirect_response(redirect_url: str) -> Response:
    """
    Creates a custom redirect response.

    Parameters
    ----------
    redirect_url : str
        The URL to which the response should redirect.

    Returns
    -------
    Response
        A response object with a 307 redirect status and the location header set.
    """

    return Response(headers={"location": redirect_url}, status_code=307)


@router.get("/login")
async def login(spotify_auth_service: SpotifyAuthServiceDependency):
    """
    Initiates the Spotify login process.

    This route generates a login URL for Spotify's OAuth authentication flow, sets a state cookie for CSRF protection
    and redirects the user to Spotify's authorization page.

    Parameters
    ----------
    spotify_auth_service : SpotifyAuthServiceDependency
        The Spotify authentication service used to generate the authorization URL.

    Returns
    -------
    Response
        A redirect response to Spotify's OAuth authorization page with a state cookie.
    """

    state = secrets.token_hex(16)
    url = spotify_auth_service.generate_auth_url(state)

    response = create_custom_redirect_response(url)
    response.set_cookie(key="oauth_state", value=state)

    return response


@router.get("/callback")
async def callback(
        code: str,
        state: str,
        request: Request,
        settings: SettingsDependency,
        spotify_auth_service: SpotifyAuthServiceDependency
):
    """
    Handles the OAuth callback from Spotify.

    After a user logs in with Spotify, this route processes the callback, verifies the state parameter to prevent CSRF
    attacks, retrieves access and refresh tokens and redirects the user back to the frontend of the application.

    If authentication fails, access and refresh tokens will not be set in the cookies and the user will be redirected
    to the authentication-failure route in the frontend.

    Parameters
    ----------
    code : str
        The authorization code returned by Spotify after a successful login.
    state : str
        The state parameter received from Spotify for CSRF validation.
    request : Request
        The FastAPI request object, used to access cookies for state validation.
    spotify_auth_service : SpotifyAuthServiceDependency
        The Spotify authentication service responsible for exchanging the authorization code for tokens.
    settings : SettingsDependency
        The application settings containing environment configuration values.

    Returns
    -------
    Response
        A redirect response to the frontend application with access and refresh tokens stored in cookies.
    """

    # make sure that state stored in login route is same as that received after authenticating
    # prevents csrf
    if request.cookies["oauth_state"] != state:
        logger.error(f"invalid state param")
        error_params = urllib.parse.urlencode({"error": "auth-failure"})
        return RedirectResponse(f"{settings.frontend_url}/#{error_params}")

    return RedirectResponse(f"{settings.frontend_url}/auth-success/?code={code}")


@router.post("/tokens", response_model=TokenData)
async def get_tokens(code: Annotated[str, Body()], spotify_auth_service: SpotifyAuthServiceDependency) -> TokenData:
    try:
        tokens = await spotify_auth_service.create_tokens(code)
        return tokens
    except SpotifyAuthServiceException as e:
        logger.error(f"Failed to create tokens from code: {code} - {e}")
        raise HTTPException(status_code=401, detail="Invalid authorisation code.")


@router.post("/refresh-tokens", response_model=TokenData)
async def get_tokens(refresh_token: Annotated[str, Body()], spotify_auth_service: SpotifyAuthServiceDependency) -> TokenData:
    try:
        tokens = await spotify_auth_service.refresh_tokens(refresh_token)
        return tokens
    except SpotifyAuthServiceException as e:
        logger.error(f"Failed to refresh tokens from refresh_token: {refresh_token} - {e}")
        raise HTTPException(status_code=401, detail="Invalid refresh token.")
