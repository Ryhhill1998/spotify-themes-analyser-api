from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Request, HTTPException

from api.models import TokenData
from api.services.analysis_service import AnalysisService
from api.services.endpoint_requester import EndpointRequester
from api.services.lyrics_service import LyricsService
from api.services.spotify.spotify_auth_service import SpotifyAuthService
from api.services.spotify.spotify_data_service import SpotifyDataService
from api.settings import Settings


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_tokens_from_cookies(request: Request) -> TokenData:
    cookies = request.cookies
    access_token = cookies.get("access_token")
    refresh_token = cookies.get("refresh_token")

    if not access_token or not refresh_token:
        raise HTTPException(status_code=400, detail="Requests must include an access token and a refresh token.")

    return TokenData(access_token=access_token, refresh_token=refresh_token)


def get_endpoint_requester(request: Request) -> EndpointRequester:
    return request.app.state.endpoint_requester


def get_spotify_auth_service(
        settings: Annotated[Settings, Depends(get_settings)],
        endpoint_requester: Annotated[EndpointRequester, Depends(get_endpoint_requester)]
) -> SpotifyAuthService:
    return SpotifyAuthService(
        client_id=settings.spotify_client_id,
        client_secret=settings.spotify_client_secret,
        base_url=settings.spotify_auth_base_url,
        redirect_uri=settings.spotify_auth_redirect_uri,
        auth_scope=settings.spotify_auth_user_scope,
        endpoint_requester=endpoint_requester
    )


def get_spotify_data_service(
        settings: Annotated[Settings, Depends(get_settings)],
        endpoint_requester: Annotated[EndpointRequester, Depends(get_endpoint_requester)],
        spotify_auth_service: Annotated[SpotifyAuthService, Depends(get_spotify_auth_service)]
) -> SpotifyDataService:
    return SpotifyDataService(
        client_id=settings.spotify_client_id,
        client_secret=settings.spotify_client_secret,
        base_url=settings.spotify_data_base_url,
        endpoint_requester=endpoint_requester,
        spotify_auth_service=spotify_auth_service
    )


def get_lyrics_service(
        settings: Annotated[Settings, Depends(get_settings)],
        endpoint_requester: Annotated[EndpointRequester, Depends(get_endpoint_requester)]
) -> LyricsService:
    return LyricsService(base_url=settings.lyrics_base_url, endpoint_requester=endpoint_requester)


def get_analysis_service(
        settings: Annotated[Settings, Depends(get_settings)],
        endpoint_requester: Annotated[EndpointRequester, Depends(get_endpoint_requester)]
) -> AnalysisService:
    return AnalysisService(base_url=settings.analysis_base_url, endpoint_requester=endpoint_requester)
