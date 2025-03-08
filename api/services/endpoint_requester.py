import json
from enum import Enum
from typing import Any
import httpx
from httpx import Response


class EndpointRequesterException(Exception):
    """
    Raised when an HTTP request fails for any reason other than a 401 status code.

    This exception is triggered when an HTTP request made using `httpx` results in
    an error that is not a 401 Unauthorized status code.

    Parameters
    ----------
    message : str, optional
        The error message describing the failure. Default is "Failed to make request".
    """

    def __init__(self, message: str = "Failed to make request"):
        super().__init__(message)


class EndpointRequesterUnauthorisedException(EndpointRequesterException):
    """
    Raised when an HTTP request fails with a 401 Unauthorized status code.

    This exception is a subclass of `EndpointRequesterException` and is
    specifically used when the response status code is 401.

    Parameters
    ----------
    message : str, optional
        The error message describing the unauthorized request. Default is "Unauthorized".
    """

    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message)


class RequestMethod(Enum):
    """
    Enum representing supported HTTP request methods.

    Attributes
    ----------
    GET : str
        Represents an HTTP GET request.
    POST : str
        Represents an HTTP POST request.
    """

    GET = "GET"
    POST = "POST"


class EndpointRequester:
    """
    A class for making HTTP requests asynchronously using `httpx.AsyncClient`.

    This class provides methods for making GET and POST requests while handling errors
    such as timeouts, invalid responses and HTTP status errors.

    Attributes
    ----------
    client : httpx.AsyncClient
        An instance of `httpx.AsyncClient` used to send requests.

    Methods
    -------
    get(url, headers=None, params=None, timeout=None)
        Sends a GET request to the specified URL.

    post(url, headers=None, data=None, json_data=None, timeout=None)
        Sends a POST request to the specified URL.
    """

    def __init__(self, client: httpx.AsyncClient):
        """
        Initializes the EndpointRequester with an `httpx.AsyncClient` instance.

        Parameters
        ----------
        client : httpx.AsyncClient
            The HTTP client used for sending requests.
        """

        self.client = client

    @staticmethod
    def _validate_and_parse_response(res: Response):
        """
        Validates and parses an HTTP response.

        This method checks whether the response contains an HTTP status error (non 2XX code), raises an exception if
        needed and returns the JSON-parsed response.

        Parameters
        ----------
        res : httpx.Response
            The response object from an HTTP request.

        Returns
        -------
        Any
            The JSON-decoded content of the response.

        Raises
        ------
        httpx.HTTPStatusError
            If the response contains an HTTP error status code.
        json.decoder.JSONDecodeError
            If the response body is not valid JSON.
        """

        res.raise_for_status()
        return res.json()

    @staticmethod
    def _handle_http_status_error(e: httpx.HTTPStatusError):
        """
        Handles HTTP status errors by raising appropriate exceptions.

        Parameters
        ----------
        e : httpx.HTTPStatusError
            The exception raised due to an HTTP status error.

        Raises
        ------
        EndpointRequesterUnauthorisedException
            If the response status code is 401 Unauthorized.
        EndpointRequesterException
            For all other non-2XX status codes.
        """

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
        """
        Sends an HTTP request asynchronously and handles errors.

        This method sends an HTTP request using the specified method, URL and optional parameters.
        It handles various exceptions, including timeout errors, invalid responses and HTTP status errors.

        Parameters
        ----------
        method : RequestMethod
            The HTTP method to use (GET or POST).
        url : str
            The URL to send the request to.
        headers : dict[str, str], optional
            Optional headers to include in the request.
        params : dict[str, str], optional
            Optional query parameters to include in the request.
        data : dict[str, Any], optional
            Optional form data to send in a POST request.
        json_data : Any, optional
            Optional JSON data to send in a POST request.
        timeout : float, optional
            Optional timeout value (in seconds) for the request.

        Returns
        -------
        Any
            The JSON-decoded response content.

        Raises
        ------
        EndpointRequesterException
            Raised for request failures, timeouts, invalid JSON responses or other errors.
        EndpointRequesterUnauthorisedException
            Raised if the request fails with a 401 Unauthorized status.
        """

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

    async def get(
            self, url: str,
            headers: dict[str, str] | None = None,
            params: dict[str, str] | None = None,
            timeout: float | None = None
    ):
        """
        Sends an asynchronous GET request.

        Parameters
        ----------
        url : str
            The URL to send the request to.
        headers : dict[str, str], optional
            Optional headers to include in the request.
        params : dict[str, str], optional
            Optional query parameters to include in the request.
        timeout : float, optional
            Optional timeout value (in seconds) for the request.

        Returns
        -------
        Any
            The JSON-decoded response content.

        Raises
        ------
        EndpointRequesterException
            Raised if the request fails.
        EndpointRequesterUnauthorisedException
            Raised if the request receives a 401 Unauthorized response.
        """

        return await self._request(method=RequestMethod.GET, url=url, headers=headers, params=params, timeout=timeout)

    async def post(
            self,
            url: str,
            headers: dict[str, str] = None,
            data: dict[str, Any] = None,
            json_data: Any | None = None,
            timeout: float | None = None
    ):
        """
        Sends an asynchronous POST request.

        Parameters
        ----------
        url : str
            The URL to send the request to.
        headers : dict[str, str], optional
            Optional headers to include in the request.
        data : dict[str, Any], optional
            Optional form data to send in the request body.
        json_data : Any, optional
            Optional JSON data to send in the request body.
        timeout : float, optional
            Optional timeout value (in seconds) for the request.

        Returns
        -------
        Any
            The JSON-decoded response content.

        Raises
        ------
        EndpointRequesterException
            Raised if the request fails.
        EndpointRequesterUnauthorisedException
            Raised if the request receives a 401 Unauthorized response.
        """

        return await self._request(
            method=RequestMethod.POST,
            url=url,
            headers=headers,
            data=data,
            json_data=json_data,
            timeout=timeout
        )
