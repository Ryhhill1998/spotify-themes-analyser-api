from typing import Annotated
from pydantic import BaseModel, Field

class TokenData(BaseModel):
    """
    Represents the Spotify authentication tokens for a user.

    Attributes
    ----------
    access_token : str
        The access token used for authenticated requests to the Spotify API.
    refresh_token : str
        The refresh token used to obtain a new access token.
    """

    access_token: str
    refresh_token: str


class SpotifyItemBase(BaseModel):
    """
    The most basic form of a Spotify item (e.g., artist or track).

    Attributes
    ----------
    id : str
        The unique identifier of the item.
    name : str
        The name of the item.
    """

    id: str
    name: str


class SpotifyItem(SpotifyItemBase):
    """
    Represents a Spotify item with additional metadata.

    Inherits from
    -------------
    SpotifyItemBase, which provides the id and name attributes.

    Attributes
    ----------
    images : list[dict]
        A list of image objects for the item.
    spotify_url : str
        The Spotify URL for the item.
    """

    images: list[dict]
    spotify_url: str


class SpotifyArtist(SpotifyItem):
    """
    Represents a Spotify artist with additional metadata.

    Inherits from
    -------------
    SpotifyItem, which provides the id, name, images and spotify_url attributes.

    Attributes
    ----------
    genres : list[str]
        A list of genres associated with the artist.
    """

    genres: list[str]


class TrackArtist(SpotifyItemBase):
    """
    Represents an artist associated with a track.

    This model is a simplified version of `SpotifyArtist`, containing only the basic artist details (ID and name).

    Inherits from
    -------------
    SpotifyItemBase, which provides the id and name attributes.
    """

    pass


class SpotifyTrack(SpotifyItem):
    """
    Represents a Spotify track with associated metadata.

    Inherits from
    -------------
    SpotifyItem, which provides the id, name, images and spotify_url attributes.

    Attributes
    ----------
    artist : TrackArtist
        The primary artist of the track.
    release_date : str
        The release date of the track.
    explicit : bool
        Indicates whether the track contains explicit content.
    duration_ms : int
        The duration of the track in milliseconds.
    popularity : int
        The popularity score of the track (0-100).
    """

    artist: TrackArtist
    release_date: str
    explicit: bool
    duration_ms: int
    popularity: int


class SpotifyItemResponse(BaseModel):
    """
    Represents a response containing a single Spotify item.

    Attributes
    ----------
    data : SpotifyItem
        The item data.
    tokens : TokenData
        The updated authentication tokens.
    """

    data: SpotifyItem
    tokens: TokenData


class SpotifyItemsResponse(BaseModel):
    """
    Represents a response containing a list of Spotify items.

    Attributes
    ----------
    data : list[SpotifyItem]
        A list of Spotify items.
    tokens : TokenData
        The updated authentication tokens.
    """

    data: list[SpotifyItem]
    tokens: TokenData


class LyricsRequest(BaseModel):
    """
    Represents a request to retrieve lyrics for a track.

    Attributes
    ----------
    track_id : str
        The unique identifier of the track.
    artist_name : str
        The name of the artist.
    track_title : str
        The title of the track.
    """

    track_id: str
    artist_name: str
    track_title: str


class LyricsResponse(LyricsRequest):
    """
    Represents a response containing the lyrics for a track.

    Inherits from
    -------------
    LyricsRequest, which provides the track_id, artist_name and track_title.

    Attributes
    ----------
    lyrics : str
        The lyrics of the requested track.
    """

    lyrics: str | None


class AnalysisRequest(BaseModel):
    """
    Represents a request for analysis of a track's lyrics.

    Attributes
    ----------
    track_id : str
        The unique identifier of the track.
    lyrics : str
        The lyrics of the track to be analyzed.
    """

    track_id: str
    lyrics: str


EmotionPercentage = Annotated[float, Field(ge=0, le=1)]
"""
A float value representing the percentage of an emotion, ranging from 0 to 1.
"""


class EmotionalAnalysis(BaseModel):
    """
    Represents the emotional analysis of a track's lyrics.

    Attributes
    ----------
    joy : float
        The percentage of joy detected in the lyrics.
    sadness : float
        The percentage of sadness detected in the lyrics.
    anger : float
        The percentage of anger detected in the lyrics.
    fear : float
        The percentage of fear detected in the lyrics.
    love : float
        The percentage of love detected in the lyrics.
    hope : float
        The percentage of hope detected in the lyrics.
    nostalgia : float
        The percentage of nostalgia detected in the lyrics.
    loneliness : float
        The percentage of loneliness detected in the lyrics.
    confidence : float
        The percentage of confidence detected in the lyrics.
    despair : float
        The percentage of despair detected in the lyrics.
    excitement : float
        The percentage of excitement detected in the lyrics.
    mystery : float
        The percentage of mystery detected in the lyrics.
    defiance : float
        The percentage of defiance detected in the lyrics.
    gratitude : float
        The percentage of gratitude detected in the lyrics.
    spirituality : float
        The percentage of spirituality detected in the lyrics.
    """

    joy: EmotionPercentage
    sadness: EmotionPercentage
    anger: EmotionPercentage
    fear: EmotionPercentage
    love: EmotionPercentage
    hope: EmotionPercentage
    nostalgia: EmotionPercentage
    loneliness: EmotionPercentage
    confidence: EmotionPercentage
    despair: EmotionPercentage
    excitement: EmotionPercentage
    mystery: EmotionPercentage
    defiance: EmotionPercentage
    gratitude: EmotionPercentage
    spirituality: EmotionPercentage


class EmotionalProfile(AnalysisRequest):
    """
    Represents the emotional profile of a track's lyrics.

    Inherits from
    -------------
    AnalysisRequest, which provides the track_id and lyrics.

    Attributes
    ----------
    emotional_analysis : EmotionalAnalysis
        The detailed emotional analysis of the lyrics.
    """

    emotional_analysis: EmotionalAnalysis


class TopEmotion(BaseModel):
    """
    Represents an emotion, the track with the highest percentage detected for this emotion and the average percentage
    of this emotion detected across all requested tracks.

    Attributes
    ----------
    name : str
        The name of the emotion.
    percentage : float
        The percentage of the emotion (0 to 1).
    track_id : str
        The unique identifier of the track.
    """

    name: str
    percentage: EmotionPercentage
    track_id: str


class TopEmotionsResponse(BaseModel):
    """
    Represents a response containing the top emotions detected across tracks.

    Attributes
    ----------
    top_emotions : list[TopEmotion]
        A list of the most prominent emotions detected in different tracks.
    tokens : TokenData
        The updated authentication tokens.
    """

    top_emotions: list[TopEmotion]
    tokens: TokenData
