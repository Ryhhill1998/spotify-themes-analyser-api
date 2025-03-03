from pydantic import BaseModel


class LyricsRequest(BaseModel):
    artist: str
    track_title: str


class LyricsResponse(LyricsRequest):
    lyrics: str


class TopItem(BaseModel):
    id: str
    name: str
    image_urls: str
    spotify_url: str


class TopArtist(TopItem):
    pass


class TopTrack(TopItem):
    artist: str
    release_date: str
    explicit: bool
    duration: int
    popularity: int


class TopItemsResponse(BaseModel):
    data: list[TopItem]
    access_token: str
    refresh_token: str
