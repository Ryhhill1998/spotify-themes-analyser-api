from typing import Annotated

from fastapi import Depends, APIRouter
from fastapi.responses import JSONResponse

from api.dependencies import get_tokens_from_cookies, get_spotify_data_service, get_spotify_auth_service, \
    get_lyrics_service, get_analysis_service, get_insights_service
from api.models import LyricsRequest, LyricsResponse, TokenData
from api.services.analysis_service import AnalysisService
from api.services.emotional_profile_service import InsightsService
from api.services.lyrics_service import LyricsService
from api.services.spotify.spotify_auth_service import SpotifyAuthService
from api.services.spotify.spotify_data_service import SpotifyDataService, TopItemType
from api.utils import set_response_cookie

router = APIRouter(prefix="/data")

# initialise dependencies
token_cookie_extraction_dependency = Annotated[TokenData, Depends(get_tokens_from_cookies)]
spotify_auth_service_dependency = Annotated[SpotifyAuthService, Depends(get_spotify_auth_service)]
spotify_data_service_dependency = Annotated[SpotifyDataService, Depends(get_spotify_data_service)]
lyrics_service_dependency = Annotated[LyricsService, Depends(get_lyrics_service)]
analysis_service_dependency = Annotated[AnalysisService, Depends(get_analysis_service)]
insights_service_dependency = Annotated[InsightsService, Depends(get_insights_service)]


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
        tokens: token_cookie_extraction_dependency,
        spotify_data_service: spotify_data_service_dependency
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
        tokens: token_cookie_extraction_dependency,
        spotify_data_service: spotify_data_service_dependency
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
        tokens: token_cookie_extraction_dependency,
        spotify_data_service: spotify_data_service_dependency
) -> JSONResponse:
    response = await get_top_items_response(
        spotify_data_service=spotify_data_service,
        tokens=tokens,
        item_type=TopItemType.ARTISTS
    )

    return response


@router.get("/top-tracks")
async def get_top_tracks(
        tokens: token_cookie_extraction_dependency,
        spotify_data_service: spotify_data_service_dependency
) -> JSONResponse:
    response = await get_top_items_response(
        spotify_data_service=spotify_data_service,
        tokens=tokens,
        item_type=TopItemType.TRACKS
    )

    return response


@router.post("/lyrics-list")
async def retrieve_lyrics_list(
        lyrics_requests: list[LyricsRequest],
        lyrics_service: lyrics_service_dependency
) -> list[LyricsResponse]:
    lyrics_list = await lyrics_service.get_lyrics_list(lyrics_requests)

    return lyrics_list


@router.get("/emotional-profile")
async def get_emotional_profile(
        tokens: token_cookie_extraction_dependency,
        insights_service: insights_service_dependency,
) -> JSONResponse:
    emotional_profile = await insights_service.get_emotional_profile(tokens)
    top_emotions = emotional_profile.emotions
    tokens = emotional_profile.tokens

    response_content = [emotion.model_dump() for emotion in top_emotions]
    response = create_json_response_and_set_token_cookies(content=response_content, tokens=tokens)

    return response
