import base64
import requests
import urllib.parse

from api.services.spotify_service import SpotifyService


class SpotifyAuthService(SpotifyService):
    def __init__(self, client_id: str, client_secret: str, base_url: str, redirect_uri: str, auth_scope: str):
        super().__init__(client_id=client_id, client_secret=client_secret, base_url=base_url)
        self.redirect_uri = redirect_uri
        self.auth_scope = auth_scope
        self.auth_header = self._generate_auth_header()

    def _generate_auth_header(self) -> str:
        return base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()

    def refresh_access_token(self, refresh_token: str) -> dict[str, str]:
        res = requests.post(
            url=f"{self.base_url}/api/token",
            headers={
                "Authorization": f"Basic {self.auth_header}",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token
            }
        )
        data = res.json()

        return {"access_token": data["access_token"], "refresh_token": data.get("refresh_token", refresh_token)}

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

    def get_tokens_with_auth_code(self, auth_code: str):
        response = requests.post(
            url=f"{self.base_url}/api/token",
            headers={
                "Authorization": f"Basic {self.auth_header}",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data={
                "code": auth_code,
                "redirect_uri": self.redirect_uri,
                "grant_type": "authorization_code"
            }
        )

        response.raise_for_status()

        token_data = response.json()
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")

        return {"access_token": access_token, "refresh_token": refresh_token}
