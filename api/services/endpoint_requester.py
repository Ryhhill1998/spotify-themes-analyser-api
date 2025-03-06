from enum import Enum
from typing import Any
import httpx
from httpx import Response


class EndpointRequesterException(Exception):
    def __init__(self, message="Failed to make request"):
        super().__init__(message)


class EndpointRequesterUnauthorisedException(EndpointRequesterException):
    def __init__(self, message="Unauthorized"):
        super().__init__(message)


class RequestMethod(Enum):
    GET = "GET"
    POST = "POST"


class EndpointRequester:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    @staticmethod
    def _validate_response(res: Response):
        if res.status_code == 401:
            print(f"Unauthorized request: {res.text}")
            raise EndpointRequesterUnauthorisedException()

        res.raise_for_status()

    @staticmethod
    def _parse_response(res: Response):
        try:
            return res.json()
        except ValueError as e:
            print(f"Invalid JSON response: {e}")
            raise EndpointRequesterException("Response not valid JSON.")

    async def _request(
            self,
            method: RequestMethod,
            url: str,
            headers: dict[str, str] | None = None,
            params: dict[str, str] | None = None,
            data: dict[str, Any] | None = None,
            json: Any | None = None,
            timeout: float | None = None
    ):
        try:
            res = await self.client.request(
                method=method.value,
                url=url,
                headers=headers,
                params=params,
                data=data,
                json=json,
                timeout=timeout
            )
        except httpx.TimeoutException as e:
            print(f"Request timeout: {e}")
            raise EndpointRequesterException("Request timed out.")
        except httpx.InvalidURL as e:
            print(f"Invalid URL: {e}")
            raise EndpointRequesterException("Invalid URL provided.")
        except httpx.RequestError as e:
            print(f"Request failed: {e}")
            raise EndpointRequesterException(f"Request failed: {str(e)}")

        self._validate_response(res)

        return self._parse_response(res)

    async def get(self, url: str, headers=None, params=None, timeout=None):
        return await self._request(method=RequestMethod.GET, url=url, headers=headers, params=params, timeout=timeout)

    async def post(self, url: str, headers=None, data=None, json=None, timeout=None):
        return await self._request(method=RequestMethod.POST, url=url, headers=headers, data=data, json=json, timeout=timeout)
