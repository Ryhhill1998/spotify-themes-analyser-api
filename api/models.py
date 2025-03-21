from enum import Enum
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


class SpotifyTrackArtist(SpotifyItemBase):
    """
    Represents an artist associated with a track.

    This model is a simplified version of `SpotifyArtist`, containing only the basic artist details (ID and name).

    Inherits from
    -------------
    SpotifyItemBase, which provides the id and name attributes.
    """

    pass


class SpotifyItemExternalUrls(BaseModel):
    """
    Represents external URLs associated with a Spotify item.

    Attributes
    ----------
    spotify : str
        The Spotify URL of the item.
    """

    spotify: str


class SpotifyItemImage(BaseModel):
    """
    Represents an image associated with a Spotify item.

    Attributes
    ----------
    height : int
        The height of the image in pixels.
    width : int
        The width of the image in pixels.
    url : str
        The URL of the image.
    """

    height: int
    width: int
    url: str


class SpotifyTrackAlbum(BaseModel):
    """
    Represents an album that a track belongs to.

    Attributes
    ----------
    images : list[SpotifyItemImage]
        A list of images representing the album cover.
    release_date : str
        The release date of the album.
    """

    images: list[SpotifyItemImage]
    release_date: str


class SpotifyTrackData(SpotifyItemBase):
    """
    Represents detailed metadata of a Spotify track.

    Inherits from
    -------------
    SpotifyItemBase
        Provides the `id` and `name` attributes.

    Attributes
    ----------
    album : SpotifyTrackAlbum
        The album the track belongs to.
    artists : list[SpotifyTrackArtist]
        A list of artists featured on the track.
    external_urls : SpotifyItemExternalUrls
        External URLs related to the track.
    explicit : bool
        Indicates whether the track contains explicit content.
    duration_ms : int
        The duration of the track in milliseconds.
    popularity : int
        The popularity score of the track (0-100).
    """

    album: SpotifyTrackAlbum
    artists: list[SpotifyTrackArtist]
    external_urls: SpotifyItemExternalUrls
    explicit: bool
    duration_ms: int
    popularity: int


class SpotifyArtistData(SpotifyItemBase):
    """
    Represents detailed metadata of a Spotify artist.

    Inherits from
    -------------
    SpotifyItemBase
        Provides the `id` and `name` attributes.

    Attributes
    ----------
    images : list[SpotifyItemImage]
        A list of images representing the artist.
    external_urls : SpotifyItemExternalUrls
        External URLs related to the artist.
    genres : list[str]
        A list of genres associated with the artist.
    """

    images: list[SpotifyItemImage]
    external_urls: SpotifyItemExternalUrls
    genres: list[str]


class SpotifyItem(SpotifyItemBase):
    """
    Represents a Spotify item with additional metadata.

    Inherits from
    -------------
    SpotifyItemBase
        Provides the `id` and `name` attributes.

    Attributes
    ----------
    images : list[SpotifyItemImage]
        A list of images associated with the item.
    spotify_url : str
        The Spotify URL of the item.
    """

    images: list[SpotifyItemImage]
    spotify_url: str


class SpotifyArtist(SpotifyItem):
    """
    Represents a Spotify artist with additional metadata.

    Inherits from
    -------------
    SpotifyItem
        Provides the `id`, `name`, `images`, and `spotify_url` attributes.

    Attributes
    ----------
    genres : list[str]
        A list of genres associated with the artist.
    """

    genres: list[str]


class SpotifyTrack(SpotifyItem):
    """
    Represents a Spotify track with associated metadata.

    Inherits from
    -------------
    SpotifyItem
        Provides the `id`, `name`, `images`, and `spotify_url` attributes.

    Attributes
    ----------
    artist : SpotifyTrackArtist
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

    artist: SpotifyTrackArtist
    release_date: str
    explicit: bool
    duration_ms: int
    popularity: int


class SpotifyItemResponse(BaseModel):
    """
    Represents a response containing a single Spotify item and updated authentication tokens.

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
    Represents a response containing a list of Spotify items and updated authentication tokens.

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

    lyrics: str


class AnalysisRequestBase(BaseModel):
    """
    Base class for requests related to track analysis.

    Attributes
    ----------
    track_id : str
        The unique identifier of the track.
    lyrics : str
        The lyrics of the track.
    """

    track_id: str
    lyrics: str


class EmotionalProfileRequest(AnalysisRequestBase):
    """
    Represents a request to analyze the emotional profile of a track.

    Inherits from
    -------------
    AnalysisRequestBase
        Provides the `track_id` and `lyrics` attributes.
    """

    pass


EmotionPercentage = Annotated[float, Field(ge=0, le=1)]
"""
A float value representing the percentage of an emotion, ranging from 0 to 1.
"""


class EmotionalProfile(BaseModel):
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


class EmotionalProfileResponse(EmotionalProfileRequest):
    """
    Represents the emotional profile of a track's lyrics.

    Inherits from
    -------------
    EmotionalProfileRequest
        Provides the `track_id` and `lyrics` attributes.

    Attributes
    ----------
    emotional_profile : EmotionalProfile
        The detailed emotional analysis of the lyrics.
    """

    emotional_profile: EmotionalProfile


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
    Represents a response containing the top emotions detected across tracks and updated spotify auth tokens.

    Attributes
    ----------
    top_emotions : list[TopEmotion]
        A list of the most prominent emotions detected in different tracks.
    tokens : TokenData
        The updated authentication tokens.
    """

    top_emotions: list[TopEmotion]
    tokens: TokenData


class Emotion(str, Enum):
    """
    Enum representing various emotions detected in track lyrics.

    Attributes
    ----------
    JOY : str
        Represents the emotion of joy.
    SADNESS : str
        Represents the emotion of sadness.
    ANGER : str
        Represents the emotion of anger.
    FEAR : str
        Represents the emotion of fear.
    LOVE : str
        Represents the emotion of love.
    HOPE : str
        Represents the emotion of hope.
    NOSTALGIA : str
        Represents the emotion of nostalgia.
    LONELINESS : str
        Represents the emotion of loneliness.
    CONFIDENCE : str
        Represents the emotion of confidence.
    DESPAIR : str
        Represents the emotion of despair.
    EXCITEMENT : str
        Represents the emotion of excitement.
    MYSTERY : str
        Represents the emotion of mystery.
    DEFIANCE : str
        Represents the emotion of defiance.
    GRATITUDE : str
        Represents the emotion of gratitude.
    SPIRITUALITY : str
        Represents the emotion of spirituality.
    """

    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    LOVE = "love"
    HOPE = "hope"
    NOSTALGIA = "nostalgia"
    LONELINESS = "loneliness"
    CONFIDENCE = "confidence"
    DESPAIR = "despair"
    EXCITEMENT = "excitement"
    MYSTERY = "mystery"
    DEFIANCE = "defiance"
    GRATITUDE = "gratitude"
    SPIRITUALITY = "spirituality"


class EmotionalTagsRequest(AnalysisRequestBase):
    """
    Represents a request for emotional tags for a track.

    Inherits from
    -------------
    AnalysisRequestBase
        Provides the `track_id` and `lyrics` attributes.

    Attributes
    ----------
    emotion : Emotion
        The emotion being analyzed.
    """

    emotion: Emotion


class EmotionalTagsResponse(EmotionalTagsRequest):
    """
    Represents a response containing emotional tags for a track.

    Inherits from
    -------------
    EmotionalTagsRequest
        Provides the `track_id`, `lyrics`, and `emotion` attributes.
    """

    pass


class TaggedLyricsResponse(BaseModel):
    """
    Represents a response containing lyrics with emotional tags and updated spotify authentication tokens.

    Attributes
    ----------
    lyrics_data : EmotionalTagsResponse
        The analyzed emotional tags associated with the lyrics.
    tokens : TokenData
        The updated authentication tokens.
    """

    lyrics_data: EmotionalTagsResponse
    tokens: TokenData
