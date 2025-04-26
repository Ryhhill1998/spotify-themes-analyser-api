import asyncio
from unittest.mock import AsyncMock, MagicMock
import pytest
from api.data_structures.models import LyricsRequest, LyricsResponse
from api.services.lyrics_service import LyricsServiceException

# 1. Test that get_lyrics_list returns [] if all get_lyrics tasks raise a LyricsServiceException.
# 2. Test that get_lyrics_list returns expected response.
# 3. Test that get_lyrics_list calls get_lyrics expected number of times.


@pytest.fixture
def mock_request_factory():
    def _create(track_id: str) -> LyricsRequest:
        return LyricsRequest(track_id=track_id, artist_name=f"Artist {track_id}", track_title=f"Track {track_id}")

    return _create


@pytest.fixture
def mock_response_factory():
    def _create(track_id: str) -> LyricsResponse:
        return LyricsResponse(
            track_id=track_id,
            artist_name=f"Artist {track_id}",
            track_title=f"Track {track_id}",
            lyrics=f"Lyrics for Track {track_id}"
        )

    return _create


@pytest.mark.asyncio
async def test_get_lyrics_list_all_failures(lyrics_service, mock_request_factory):
    lyrics_service.get_lyrics = AsyncMock(side_effect=LyricsServiceException)
    mock_requests = [mock_request_factory(str(i)) for i in range(1, 6)]

    res = await lyrics_service.get_lyrics_list(mock_requests)

    assert res == []


@pytest.mark.parametrize("exception_indices", [[], [0], [1], [2], [0, 1], [0, 2], [1, 2], [0, 1, 2]])
@pytest.mark.asyncio
async def test_get_lyrics_list_returns_expected_response(
        lyrics_service,
        mock_request_factory,
        mock_response_factory,
        exception_indices
):
    # ARRANGE
    mock_requests = [mock_request_factory(str(i)) for i in range(1, 4)]
    mock_task_list = [asyncio.Future(), asyncio.Future(), asyncio.Future()]
    lyrics_service._create_lyrics_tasks = MagicMock(return_value=mock_task_list)

    mock_exception = LyricsServiceException("Test")
    mock_responses = [mock_response_factory(str(i)) for i in range(1, 4)]
    for index in exception_indices:
        mock_responses[index] = mock_exception

    for index, response in enumerate(mock_responses):
        future_return_value = mock_task_list[index]

        if isinstance(response, Exception):
            future_return_value.set_exception(response)
        else:
            future_return_value.set_result(response)

    # ACT
    res = await lyrics_service.get_lyrics_list(mock_requests)

    # ASSERT
    full_response = [
        LyricsResponse(
            track_id="1",
            artist_name="Artist 1",
            track_title="Track 1",
            lyrics="Lyrics for Track 1"
        ),
        LyricsResponse(
            track_id="2",
            artist_name="Artist 2",
            track_title="Track 2",
            lyrics="Lyrics for Track 2"
        ),
        LyricsResponse(
            track_id="3",
            artist_name="Artist 3",
            track_title="Track 3",
            lyrics="Lyrics for Track 3"
        )
    ]
    exception_indices_set = set(exception_indices)
    expected_response = [res for index, res in enumerate(full_response) if index not in exception_indices_set]
    assert res == expected_response


@pytest.mark.asyncio
async def test_get_lyrics_list_calls_get_lyrics_expected_times(
        lyrics_service,
        mock_request_factory,
        mock_response_factory
):
    mock_requests = [mock_request_factory(str(i)) for i in range(1, 6)]
    mock_response = [mock_response_factory(str(i)) for i in range(1)].pop()
    task = asyncio.Future()
    task.set_result(mock_response)
    lyrics_service.get_lyrics = MagicMock(return_value=task)

    await lyrics_service.get_lyrics_list(mock_requests)

    assert lyrics_service.get_lyrics.call_count == len(mock_requests)

