from typing import Annotated

from pydantic import BaseModel, Field


class TokenData(BaseModel):
    access_token: str
    refresh_token: str


class TopItemBase(BaseModel):
    id: str
    name: str


class TopItem(TopItemBase):
    images: list[dict]
    spotify_url: str


class TopArtist(TopItem):
    genres: list[str]


class TrackArtist(TopItemBase):
    pass


class TopTrack(TopItem):
    artist: TrackArtist
    release_date: str
    explicit: bool
    duration_ms: int
    popularity: int


class TopItemResponse(BaseModel):
    data: TopItem
    tokens: TokenData


class TopItemsResponse(BaseModel):
    data: list[TopItem]
    tokens: TokenData


class LyricsRequest(BaseModel):
    track_id: str
    artist_name: str
    track_title: str


class LyricsResponse(LyricsRequest):
    lyrics: str


class AnalysisRequest(BaseModel):
    track_id: str
    lyrics: str


EmotionPercentage = Annotated[float, Field(ge=0, le=1)]


class Emotion(BaseModel):
    name: str
    percentage: EmotionPercentage
    track_id: str


class EmotionalProfileResponse(BaseModel):
    emotions: list[Emotion]
    tokens: TokenData

