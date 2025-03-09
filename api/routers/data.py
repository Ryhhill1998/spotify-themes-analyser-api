from fastapi import APIRouter
from fastapi.responses import JSONResponse

from api.dependencies import TokenCookieExtractionDependency, SpotifyDataServiceDependency, InsightsServiceDependency
from api.models import TokenData
from api.services.music.spotify_data_service import SpotifyDataService, ItemType
from api.utils import set_response_cookie

router = APIRouter(prefix="/data")


def create_json_response_and_set_token_cookies(content: list[dict] | dict, tokens: TokenData) -> JSONResponse:
    response = JSONResponse(content=content)
    set_response_cookie(response=response, key="access_token", value=tokens.access_token)
    set_response_cookie(response=response, key="refresh_token", value=tokens.refresh_token)

    return response


async def get_item_response(
        item_id: str,
        item_type: ItemType,
        tokens: TokenData,
        spotify_data_service: SpotifyDataService
) -> JSONResponse:
    top_item_response = await spotify_data_service.get_item_by_id(item_id=item_id, tokens=tokens, item_type=item_type)
    tokens = top_item_response.tokens

    response_content = top_item_response.data.model_dump()
    response = create_json_response_and_set_token_cookies(content=response_content, tokens=tokens)

    return response


@router.get("/tracks/{track_id}")
async def get_track_by_id(
        track_id: str,
        tokens: TokenCookieExtractionDependency,
        spotify_data_service: SpotifyDataServiceDependency
) -> JSONResponse:
    track_response = await get_item_response(
        item_id=track_id,
        item_type=ItemType.TRACKS,
        tokens=tokens,
        spotify_data_service=spotify_data_service
    )

    return track_response


@router.get("/artists/{artist_id}")
async def get_artist_by_id(
        artist_id: str,
        tokens: TokenCookieExtractionDependency,
        spotify_data_service: SpotifyDataServiceDependency
) -> JSONResponse:
    artist_response = await get_item_response(
        item_id=artist_id,
        item_type=ItemType.ARTISTS,
        tokens=tokens,
        spotify_data_service=spotify_data_service
    )

    return artist_response


async def get_top_items_response(
        spotify_data_service: SpotifyDataService,
        tokens: TokenData,
        item_type: ItemType
) -> JSONResponse:
    top_items_response = await spotify_data_service.get_top_items(
        tokens=tokens,
        item_type=item_type
    )
    tokens = top_items_response.tokens

    response_content = [item.model_dump() for item in top_items_response.data]
    response = create_json_response_and_set_token_cookies(content=response_content, tokens=tokens)

    return response


@router.get("/top-artists")
async def get_top_artists(
        tokens: TokenCookieExtractionDependency,
        spotify_data_service: SpotifyDataServiceDependency
) -> JSONResponse:
    response = await get_top_items_response(
        spotify_data_service=spotify_data_service,
        tokens=tokens,
        item_type=ItemType.ARTISTS
    )

    return response


@router.get("/top-tracks")
async def get_top_tracks(
        tokens: TokenCookieExtractionDependency,
        spotify_data_service: SpotifyDataServiceDependency
) -> JSONResponse:
    response = await get_top_items_response(
        spotify_data_service=spotify_data_service,
        tokens=tokens,
        item_type=ItemType.TRACKS
    )

    return response


@router.get("/top-emotions")
async def get_top_emotions(
        tokens: TokenCookieExtractionDependency,
        insights_service: InsightsServiceDependency,
) -> JSONResponse:
    top_emotions_response = await insights_service.get_top_emotions(tokens)
    top_emotions = top_emotions_response.top_emotions
    tokens = top_emotions_response.tokens

    response_content = [emotion.model_dump() for emotion in top_emotions]
    response = create_json_response_and_set_token_cookies(content=response_content, tokens=tokens)

    return response
