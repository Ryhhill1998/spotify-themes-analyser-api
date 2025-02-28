from pydantic import BaseModel


class TrackRequest(BaseModel):
    artist: str
    track_title: str


class LyricsResponse(TrackRequest):
    lyrics: str
