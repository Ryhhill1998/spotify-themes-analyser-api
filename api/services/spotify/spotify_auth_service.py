import base64
import urllib.parse

from api.services.endpoint_requester import EndpointRequester
from api.services.spotify.spotify_service import SpotifyService


class SpotifyAuthService(SpotifyService):
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

    async def refresh_access_token(self, refresh_token: str) -> dict[str, str]:
        url = f"{self.base_url}/api/token"
        headers = {"Authorization": f"Basic {self.auth_header}", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"grant_type": "refresh_token", "refresh_token": refresh_token}

        token_data = await self.endpoint_requester.post(url=url, headers=headers, data=data)

        return {
            "access_token": token_data["access_token"],
            "refresh_token": token_data.get("refresh_token", refresh_token)
        }

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

    async def get_tokens_with_auth_code(self, auth_code: str):
        url = f"{self.base_url}/api/token"
        headers = {"Authorization": f"Basic {self.auth_header}", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"code": auth_code, "redirect_uri": self.redirect_uri, "grant_type": "authorization_code"}

        token_data = await self.endpoint_requester.post(url=url, headers=headers, data=data)

        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")

        return {"access_token": access_token, "refresh_token": refresh_token}
