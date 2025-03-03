from pydantic import BaseModel


class TokenData(BaseModel):
    access_token: str
    refresh_token: str


class LyricsRequest(BaseModel):
    artist: str
    track_title: str


class LyricsResponse(LyricsRequest):
    lyrics: str


class TopItem(BaseModel):
    id: str
    name: str
    images: list[dict]
    spotify_url: str


class TopArtist(TopItem):
    genres: list[str]


class TopTrack(TopItem):
    artist: str
    release_date: str
    explicit: bool
    duration_ms: int
    popularity: int


class TopItemsResponse(BaseModel):
    data: list[TopItem]
    tokens: TokenData
