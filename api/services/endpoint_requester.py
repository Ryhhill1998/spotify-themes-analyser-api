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

    async def get(self, url: str, headers: dict[str, str]):
        res = await self.client.get(url=url, headers=headers)
        return self._parse_response(res)

    async def post(self, url: str, headers: dict[str, str], data: dict[str, str]):
        res = await self.client.post(url=url, headers=headers, data=data)
        return self._parse_response(res)
