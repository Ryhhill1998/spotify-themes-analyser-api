from functools import lru_cache
from typing import Annotated

import psycopg2
from fastapi import Depends, Request, HTTPException

from api.services.analysis_service import AnalysisService
from api.services.db_service import DBService
from api.services.insights_service import InsightsService
from api.services.endpoint_requester import EndpointRequester
from api.services.lyrics_service import LyricsService
from api.services.music.spotify_auth_service import SpotifyAuthService
from api.services.music.spotify_data_service import SpotifyDataService
from api.settings import Settings


@lru_cache
def get_settings() -> Settings:
    return Settings()


SettingsDependency = Annotated[Settings, Depends(get_settings)]


def get_token_from_cookies(request: Request, token_key: str) -> str:
    cookies = request.cookies
    token = cookies.get(token_key)

    if not token:
        raise HTTPException(status_code=401, detail="Requests must include an access token.")

    return token


def get_access_token_from_cookies(request: Request) -> str:
    return get_token_from_cookies(request=request, token_key="access_token")


AccessTokenDependency = Annotated[str, Depends(get_access_token_from_cookies)]


def get_refresh_token_from_cookies(request: Request) -> str:
    return get_token_from_cookies(request=request, token_key="refresh_token")


RefreshTokenDependency = Annotated[str, Depends(get_refresh_token_from_cookies)]


def get_endpoint_requester(request: Request) -> EndpointRequester:
    return request.app.state.endpoint_requester


EndpointRequesterDependency = Annotated[EndpointRequester, Depends(get_endpoint_requester)]


def get_db_service(settings: SettingsDependency) -> DBService:
    conn = psycopg2.connect(
        host=settings.db_host,
        database=settings.db_name,
        user=settings.db_user,
        password=settings.db_pass
    )
    return DBService(conn)


def get_spotify_auth_service(
        settings: SettingsDependency,
        endpoint_requester: EndpointRequesterDependency
) -> SpotifyAuthService:
    return SpotifyAuthService(
        client_id=settings.spotify_client_id,
        client_secret=settings.spotify_client_secret,
        base_url=settings.spotify_auth_base_url,
        redirect_uri=settings.spotify_auth_redirect_uri,
        auth_scope=settings.spotify_auth_user_scope,
        endpoint_requester=endpoint_requester
    )


SpotifyAuthServiceDependency = Annotated[SpotifyAuthService, Depends(get_spotify_auth_service)]


def get_spotify_data_service(
        settings: SettingsDependency,
        endpoint_requester: EndpointRequesterDependency,
        access_token: AccessTokenDependency
) -> SpotifyDataService:
    return SpotifyDataService(
        client_id=settings.spotify_client_id,
        client_secret=settings.spotify_client_secret,
        base_url=settings.spotify_data_base_url,
        endpoint_requester=endpoint_requester,
        access_token=access_token
    )


SpotifyDataServiceDependency = Annotated[SpotifyDataService, Depends(get_spotify_data_service)]


def get_lyrics_service(
        settings: SettingsDependency,
        endpoint_requester: EndpointRequesterDependency
) -> LyricsService:
    return LyricsService(base_url=settings.lyrics_base_url, endpoint_requester=endpoint_requester)


LyricsServiceDependency = Annotated[LyricsService, Depends(get_lyrics_service)]


def get_analysis_service(
        settings: SettingsDependency,
        endpoint_requester: EndpointRequesterDependency
) -> AnalysisService:
    return AnalysisService(base_url=settings.analysis_base_url, endpoint_requester=endpoint_requester)


AnalysisServiceDependency = Annotated[AnalysisService, Depends(get_analysis_service)]


def get_insights_service(
        spotify_data_service: SpotifyDataServiceDependency,
        lyrics_service: LyricsServiceDependency,
        analysis_service: AnalysisServiceDependency
) -> InsightsService:
    return InsightsService(
        spotify_data_service=spotify_data_service,
        lyrics_service=lyrics_service,
        analysis_service=analysis_service
    )


InsightsServiceDependency = Annotated[InsightsService, Depends(get_insights_service)]
