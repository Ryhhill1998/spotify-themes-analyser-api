import urllib.parse
from typing import Annotated

import requests
from fastapi import Request, Depends, APIRouter
from fastapi.responses import JSONResponse

from api.dependencies import get_auth_header, get_settings
from api.settings import Settings
from api.utils import refresh_access_token, set_response_cookie

router = APIRouter(prefix="/data")


@router.get("/top-tracks")
async def get_top_tracks(
        request: Request,
        auth_header: Annotated[str, Depends(get_auth_header)],
        settings: Annotated[Settings, Depends(get_settings)]
):
    cookies = request.cookies
    access_token = cookies.get("access_token")
    refresh_token = cookies.get("refresh_token")

    params = {"time_range": "medium_term", "limit": 10}
    url = f"{settings.spotify_data_base_url}/me/top/tracks?" + urllib.parse.urlencode(params)

    res = requests.get(url=url, headers={"Authorization": f"Bearer {access_token}"})

    if res.status_code == 401:
        refresh_data = refresh_access_token(auth_header=auth_header, refresh_token=refresh_token)
        access_token = refresh_data["access_token"]
        refresh_token = refresh_data["refresh_token"]
        res = requests.get(url=url, headers={"Authorization": f"Bearer {access_token}"})

    response = JSONResponse(content=res.json())
    set_response_cookie(response=response, key="access_token", value=access_token)
    set_response_cookie(response=response, key="refresh_token", value=refresh_token)

    return response
