from abc import ABC

from api.services.endpoint_requester import EndpointRequester


class SpotifyService(ABC):
    def __init__(self, client_id: str, client_secret: str, base_url: str, endpoint_requester: EndpointRequester):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url
        self.endpoint_requester = endpoint_requester
