import base64
import urllib.parse

from api.models import TokenData
from api.services.endpoint_requester import EndpointRequester
from api.services.music.music_service import MusicService


class SpotifyAuthService(MusicService):
    def __init__(
            self,
            client_id: str,
            client_secret: str,
            base_url: str,
            redirect_uri: str,
            auth_scope: str,
            endpoint_requester: EndpointRequester
    ):
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            base_url=base_url,
            endpoint_requester=endpoint_requester
        )
        self.redirect_uri = redirect_uri
        self.auth_scope = auth_scope
        self.auth_header = self._generate_auth_header()

    def _generate_auth_header(self) -> str:
        return base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()

    def generate_auth_url(self, state: str) -> str:
        scope = self.auth_scope

        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": scope,
            "state": state
        }

        return f"{self.base_url}/authorize?" + urllib.parse.urlencode(params)

    async def _get_tokens(self, data: dict[str, str], refresh_token: str | None = None) -> TokenData:
        url = f"{self.base_url}/api/token"
        headers = {"Authorization": f"Basic {self.auth_header}", "Content-Type": "application/x-www-form-urlencoded"}

        token_data = await self.endpoint_requester.post(url=url, headers=headers, data=data)

        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token", refresh_token)

        return TokenData(access_token=access_token, refresh_token=refresh_token)

    async def refresh_tokens(self, refresh_token: str) -> TokenData:
        data = {"grant_type": "refresh_token", "refresh_token": refresh_token}

        tokens = await self._get_tokens(data=data, refresh_token=refresh_token)

        return tokens

    async def create_tokens(self, auth_code: str) -> TokenData:
        data = {"code": auth_code, "redirect_uri": self.redirect_uri, "grant_type": "authorization_code"}

        tokens = await self._get_tokens(data=data)

        return tokens
