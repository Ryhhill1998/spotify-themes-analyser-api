import requests
from fastapi import Response


def refresh_access_token(auth_header: str, refresh_token: str):
    res = requests.post(
        url="https://accounts.spotify.com/api/token",
        headers={
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded"
        },
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
    )
    data = res.json()
    return {"access_token": data["access_token"], "refresh_token": data.get("refresh_token", refresh_token)}


def set_response_cookie(response: Response, key: str, value: str):
    response.set_cookie(key=key, value=value, httponly=True, secure=False, samesite="lax")
