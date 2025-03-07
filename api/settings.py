from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    spotify_client_id: str
    spotify_client_secret: str
    spotify_auth_user_scope: str
    spotify_auth_redirect_uri: str
    spotify_auth_base_url: str
    spotify_data_base_url: str
    frontend_url: str

    lyrics_base_url: str
    analysis_base_url: str

    allowed_origins: list[str]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
