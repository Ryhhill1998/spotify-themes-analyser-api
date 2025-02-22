import base64
from functools import lru_cache
from typing import Annotated
from fastapi import Depends
from api.settings import Settings


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_auth_header(settings: Annotated[Settings, Depends(get_settings)]) -> str:
    return base64.b64encode(f"{settings.spotify_client_id}:{settings.spotify_client_secret}".encode()).decode()
