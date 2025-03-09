import secrets
import urllib.parse
from requests.exceptions import HTTPError

from fastapi import Response, APIRouter, Request, HTTPException, status
from fastapi.responses import RedirectResponse

from api.dependencies import SpotifyAuthServiceDependency, SettingsDependency
from api.utils import set_response_cookie

router = APIRouter(prefix="/auth")


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


def generate_state() -> str:
    """
    Generates a random state token for OAuth authentication.

    Returns
    -------
    str
        A randomly generated hexadecimal string to be used as a state parameter in OAuth.
    """

    return secrets.token_hex(16)


def validate_state(stored_state: str, received_state: str):
    """
    Validates the OAuth state to prevent CSRF attacks.

    Parameters
    ----------
    stored_state : str
        The state stored in the user's cookies during the login request.
    received_state : str
        The state received in the callback request.

    Raises
    ------
    ValueError
        If the stored state does not match the received state.
    """

    if stored_state != received_state:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not authenticate request.")


@router.get("/music/login")
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

    state = generate_state()
    url = spotify_auth_service.generate_auth_url(state)

    response = create_custom_redirect_response(url)
    set_response_cookie(response=response, key="oauth_state", value=state)

    return response


@router.get("/music/callback")
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

    Raises
    ------
    HTTPError
        If there is an error during the token exchange process with Spotify.
    ValueError
        If the state validation fails, indicating a potential CSRF attack.
    """

    try:
        # make sure that state stored in login route is same as that received after authenticating
        # prevents csrf
        validate_state(stored_state=request.cookies["oauth_state"], received_state=state)

        # get access and refresh tokens from music API to allow future API calls on behalf of the user
        tokens = await spotify_auth_service.create_tokens(code)

        response = create_custom_redirect_response(settings.frontend_url)
        set_response_cookie(response=response, key="access_token", value=tokens.access_token)
        set_response_cookie(response=response, key="refresh_token", value=tokens.refresh_token)

        return response
    except (HTTPError, ValueError):
        error_params = urllib.parse.urlencode({"error": "authentication-failure"})
        return RedirectResponse(f"{settings.frontend_url}/#{error_params}")
