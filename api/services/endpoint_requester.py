import requests
from requests import Response


class EndpointRequester:
    def __init__(self):
        self.client = requests.Session()

    @staticmethod
    def _parse_response(res: Response):
        res.raise_for_status()
        data = res.json()
        return data

    def get(self, url: str, headers: dict[str, str]):
        res = self.client.get(url=url, headers=headers)
        return self._parse_response(res)

    def post(self, url: str, headers: dict[str, str], data: dict[str, str]):
        res = self.client.post(url=url, headers=headers, data=data)
        return self._parse_response(res)
