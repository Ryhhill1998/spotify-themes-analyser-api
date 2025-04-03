import secrets
import urllib.parse

from fastapi import Response, APIRouter, Request
from fastapi.responses import RedirectResponse
from loguru import logger
from starlette.responses import JSONResponse

from api.dependencies import SpotifyAuthServiceDependency, SettingsDependency
from api.services.music.spotify_auth_service import SpotifyAuthServiceException
from api.routers.utils import set_response_cookie

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
async def login(spotify_auth_service: SpotifyAuthServiceDependency, settings: SettingsDependency):
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
    set_response_cookie(response=response, key="oauth_state", value=state)

    return response


@router.get("/callback")
async def callback(
        code: str,
        state: str,
        request: Request,
        spotify_auth_service: SpotifyAuthServiceDependency,
        settings: SettingsDependency
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

    try:
        # make sure that state stored in login route is same as that received after authenticating
        # prevents csrf
        if request.cookies["oauth_state"] != state:
            raise ValueError("Could not authenticate request.")

        # get access and refresh tokens from music API to allow future API calls on behalf of the user
        tokens = await spotify_auth_service.create_tokens(code)

        response = create_custom_redirect_response(settings.frontend_url)
        set_response_cookie(response=response, key="access_token", value=tokens.access_token, domain=settings.domain)
        set_response_cookie(response=response, key="refresh_token", value=tokens.refresh_token, domain=settings.domain)

        return response
    except (SpotifyAuthServiceException, ValueError) as e:
        logger.exception(f"Failed to authorise the user - {e}")
        error_params = urllib.parse.urlencode({"error": "authentication-failure"})
        return RedirectResponse(f"{settings.frontend_url}/#{error_params}")


@router.get("/cookies")
def test_set_cookies(settings: SettingsDependency):
    response = create_custom_redirect_response(settings.frontend_url)
    set_response_cookie(response=response, key="cookie1", value="val1", domain=settings.domain)
    set_response_cookie(response=response, key="cookie2", value="val2", domain=settings.domain)

    return response
