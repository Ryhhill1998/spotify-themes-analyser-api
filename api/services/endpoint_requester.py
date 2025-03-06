import json
from enum import Enum
from typing import Any
import httpx
from httpx import Response


class EndpointRequesterException(Exception):
    def __init__(self, message: str = "Failed to make request"):
        super().__init__(message)


class EndpointRequesterUnauthorisedException(EndpointRequesterException):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message)


class RequestMethod(Enum):
    GET = "GET"
    POST = "POST"


class EndpointRequester:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    @staticmethod
    def _validate_and_parse_response(res: Response):
        res.raise_for_status()
        return res.json()

    @staticmethod
    def _handle_http_status_error(e: httpx.HTTPStatusError):
        if e.response.status_code == 401:
            print(f"Unauthorized request: {e}")
            raise EndpointRequesterUnauthorisedException()

        print("Request failed.")
        raise EndpointRequesterException()

    async def _request(
            self,
            method: RequestMethod,
            url: str,
            headers: dict[str, str] | None = None,
            params: dict[str, str] | None = None,
            data: dict[str, Any] | None = None,
            json_data: Any | None = None,
            timeout: float | None = None
    ):
        try:
            res = await self.client.request(
                method=method.value,
                url=url,
                headers=headers,
                params=params,
                data=data,
                json=json_data,
                timeout=timeout
            )
            return self._validate_and_parse_response(res)
        except json.decoder.JSONDecodeError as e:
            print(f"Invalid JSON response: {e}")
            raise EndpointRequesterException("Response not valid JSON.")
        except httpx.TimeoutException as e:
            print(f"Request timeout: {e}")
            raise EndpointRequesterException("Request timed out.")
        except httpx.RequestError as e:
            print(f"Request failed: {e}")
            raise EndpointRequesterException(f"Request failed: {str(e)}")
        except httpx.HTTPStatusError as e:
            self._handle_http_status_error(e)
        except httpx.InvalidURL as e:
            print(f"Invalid URL: {e}")
            raise EndpointRequesterException("Invalid URL provided.")

    async def get(self, url: str, headers=None, params=None, timeout=None):
        return await self._request(method=RequestMethod.GET, url=url, headers=headers, params=params, timeout=timeout)

    async def post(self, url: str, headers=None, data=None, json_data=None, timeout=None):
        return await self._request(
            method=RequestMethod.POST,
            url=url,
            headers=headers,
            data=data,
            json_data=json_data,
            timeout=timeout
        )
