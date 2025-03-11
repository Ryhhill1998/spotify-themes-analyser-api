from abc import ABC

from api.services.endpoint_requester import EndpointRequester


class MusicService(ABC):
    """
    Abstract base class for music service integrations.

    This class provides a foundation for implementing music services that interact with external APIs such as Spotify.
    It defines common attributes needed for authentication and making API requests.

    Attributes
    ----------
    client_id : str
        The client ID used for authenticating with the music service API.
    client_secret : str
        The client secret used for authenticating with the music service API.
    base_url : str
        The base URL of the music service API.
    endpoint_requester : EndpointRequester
        An instance of `EndpointRequester` used to send HTTP requests to the API.
    """

    def __init__(self, client_id: str, client_secret: str, base_url: str, endpoint_requester: EndpointRequester):
        """
        Parameters
        ----------
        client_id : str
            The client ID for the music service.
        client_secret : str
            The client secret for the music service.
        base_url : str
            The base URL of the music service API.
        endpoint_requester : EndpointRequester
            The HTTP requester service used to interact with the API.
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url
        self.endpoint_requester = endpoint_requester
