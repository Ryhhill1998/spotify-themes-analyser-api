from fastapi import APIRouter
from fastapi.responses import JSONResponse

from api.dependencies import TokenCookieExtractionDependency, SpotifyDataServiceDependency, InsightsServiceDependency
from api.models import TokenData
from api.services.spotify.spotify_data_service import SpotifyDataService, TopItemType
from api.utils import set_response_cookie

router = APIRouter(prefix="/data")


def create_json_response_and_set_token_cookies(content: list[dict] | dict, tokens: TokenData) -> JSONResponse:
    response = JSONResponse(content=content)
    set_response_cookie(response=response, key="access_token", value=tokens.access_token)
    set_response_cookie(response=response, key="refresh_token", value=tokens.refresh_token)

    return response


async def get_item_response(
        item_id: str,
        item_type: TopItemType,
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
        item_type=TopItemType.TRACKS,
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
        item_type=TopItemType.ARTISTS,
        tokens=tokens,
        spotify_data_service=spotify_data_service
    )

    return artist_response


async def get_top_items_response(
        spotify_data_service: SpotifyDataService,
        tokens: TokenData,
        item_type: TopItemType
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
        item_type=TopItemType.ARTISTS
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
        item_type=TopItemType.TRACKS
    )

    return response


@router.get("/emotional-profile")
async def get_emotional_profile(
        tokens: TokenCookieExtractionDependency,
        insights_service: InsightsServiceDependency,
) -> JSONResponse:
    emotional_profile = await insights_service.get_emotional_profile(tokens)
    top_emotions = emotional_profile.emotions
    tokens = emotional_profile.tokens

    response_content = [emotion.model_dump() for emotion in top_emotions]
    response = create_json_response_and_set_token_cookies(content=response_content, tokens=tokens)

    return response
