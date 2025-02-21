from functools import lru_cache
from typing import Annotated
from fastapi import Depends, Request, HTTPException

from api.services.spotify_auth_service import SpotifyAuthService
from api.services.spotify_data_service import SpotifyDataService
from api.settings import Settings


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_tokens_from_cookies(request: Request) -> tuple[str, str]:
    cookies = request.cookies
    access_token = cookies.get("access_token")
    refresh_token = cookies.get("refresh_token")

    if not access_token or not refresh_token:
        raise HTTPException(status_code=400, detail="Requests must include an access token and a refresh token.")

    return access_token, refresh_token


def get_spotify_auth_service(settings: Annotated[Settings, Depends(get_settings)]) -> SpotifyAuthService:
    return SpotifyAuthService(
        client_id=settings.spotify_client_id,
        client_secret=settings.spotify_client_secret,
        base_url=settings.spotify_auth_base_url,
        redirect_uri=settings.spotify_auth_redirect_uri,
        auth_scope=settings.spotify_auth_user_scope
    )


def get_spotify_data_service(settings: Annotated[Settings, Depends(get_settings)]) -> SpotifyDataService:
    return SpotifyDataService(
        client_id=settings.spotify_client_id,
        client_secret=settings.spotify_client_secret,
        base_url=settings.spotify_auth_base_url
    )
