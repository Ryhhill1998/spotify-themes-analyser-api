from api.services.music.spotify_data_service import SpotifyDataServiceNotFoundException, SpotifyDataServiceException

BASE_URL = "/data/artists"


# -------------------- GET ARTIST BY ID -------------------- #
# 1. Test that /data/artists/{artist_id} returns 404 status code if Spotify artist not found.
# 2. Test that /data/artists/{artist_id} returns 500 status code if a SpotifyDataServiceException occurs.
# 3. Test that /data/artists/{artist_id} returns expected response.
def test_get_artist_by_id_404(client, mock_spotify_data_service):
    mock_spotify_data_service.get_item_by_id.side_effect = SpotifyDataServiceNotFoundException("Test")

    res = client.get(f"{BASE_URL}/1")

    assert res.status_code == 404 and res.json() == {"detail": "Could not find the requested item"}


def test_get_artist_by_id_500(client, mock_spotify_data_service):
    mock_spotify_data_service.get_item_by_id.side_effect = SpotifyDataServiceException("Test")

    res = client.get(f"{BASE_URL}/1")

    assert res.status_code == 500 and res.json() == {"detail": "Failed to retrieve the requested item"}


def test_get_artist_by_id_success(client, mock_spotify_data_service, mock_item_response):
    mock_spotify_data_service.get_item_by_id.return_value = mock_item_response

    res = client.get(f"{BASE_URL}/1")

    set_cookie_headers = res.headers.get("set-cookie")
    assert (
            res.status_code == 200 and
            res.json() == {"id": "1"} and
            "new_access" in set_cookie_headers and
            "new_refresh" in set_cookie_headers
    )
