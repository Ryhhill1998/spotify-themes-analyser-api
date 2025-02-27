import httpx
from httpx import Response


class EndpointRequester:
    def __init__(self):
        self.client = httpx.AsyncClient()

    @staticmethod
    def _parse_response(res: Response):
        res.raise_for_status()
        data = res.json()
        return data

    async def get(self, url: str, headers: dict[str, str] | None = None, params: dict[str, str] | None = None):
        res = await self.client.get(url=url, headers=headers, params=params, timeout=None)
        return self._parse_response(res)

    async def post(self, url: str, data: dict[str, str], headers: dict[str, str] | None = None):
        res = await self.client.post(url=url, headers=headers, data=data, timeout=None)
        return self._parse_response(res)
