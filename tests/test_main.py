import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.services.endpoint_requester import EndpointRequester


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, follow_redirects=False)


def test_health_check_success(client):
    res = client.get("/")

    assert res.status_code == 200 and res.json() == {"status": "running"}


def test_endpoint_requester_created_at_startup(client):
    with client:
        client.get("/")

        assert isinstance(client.app.state.endpoint_requester, EndpointRequester)
