from collections import defaultdict
from api.models import AnalysisRequest, Emotion
from api.services.endpoint_requester import EndpointRequester


class AnalysisServiceException(Exception):
    """Raised when AnalysisService fails to process the API response."""

    def __init__(self, message):
        super().__init__(message)


class AnalysisService:
    def __init__(self, base_url: str, endpoint_requester: EndpointRequester):
        """
        Service for retrieving emotional profile analysis from an external API.

        Args:
            base_url (str): The base URL of the API.
            endpoint_requester (EndpointRequester): Handles API requests.
        """
        self.base_url = base_url
        self.endpoint_requester = endpoint_requester

    @staticmethod
    def _aggregate_emotions(emotions_data: list[dict]):
        """
        Aggregates emotional scores from multiple tracks.

        Args:
            emotions_data (list[dict]): List of emotional profiles for tracks.

        Returns:
            dict: Aggregated emotion data, including total scores and max-percentage track for each emotion.
        """
        total_emotions = defaultdict(
            lambda: {
                "total": 0,
                "max_track": {"track_id": None, "percentage": 0}
            }
        )

        for entry in emotions_data:
            emotional_profile = entry["emotional_profile"]

            for emotion, percentage in emotional_profile.items():
                total_emotions[emotion]["total"] += percentage

                if percentage > total_emotions[emotion]["max_track"]["percentage"]:
                    total_emotions[emotion]["max_track"] = {"track_id": entry["track_id"], "percentage": percentage}

        return total_emotions

    @staticmethod
    def _get_average_emotions(total_emotions: dict, result_count: int) -> list[Emotion]:
        """
        Calculates the average percentage for each emotion.

        Args:
            total_emotions (dict): Aggregated emotion data.
            result_count (int): Number of tracks analyzed.

        Returns:
            list[Emotion]: List of emotions with average percentage.
        """
        try:
            return [
                Emotion(
                    name=emotion,
                    percentage=round(info["total"] / result_count, 2),
                    track_id=info["max_track"]["track_id"]
                )
                for emotion, info in total_emotions.items()
                if info["max_track"]["track_id"] is not None
            ]
        except Exception as e:
            raise AnalysisServiceException(f"Failed to calculate average emotions: {e}")

    @staticmethod
    def _get_top_emotions(emotions: list[Emotion], limit: int) -> list[Emotion]:
        """
        Returns the top N emotions based on percentage.

        Args:
            emotions (list[Emotion]): List of averaged emotions.
            limit (int): Number of top emotions to return.

        Returns:
            list[Emotion]: Sorted list of top emotions.
        """
        return sorted(emotions, key=lambda e: e.percentage, reverse=True)[:limit]

    async def get_top_emotions(self, analysis_requests: list[AnalysisRequest], limit: int = 5):
        """
        Fetches emotional profiles for a list of tracks and returns the top emotions.

        Args:
            analysis_requests (list[AnalysisRequest]): List of analysis requests.
            limit (int, optional): Number of top emotions to return. Defaults to 5.

        Returns:
            list[Emotion]: List of top emotions.

        Raises:
            AnalysisServiceException: If response parsing fails.
        """
        url = f"{self.base_url}/emotional-profile"

        data = await self.endpoint_requester.post(
            url=url,
            json_data=[item.model_dump() for item in analysis_requests],
            timeout=None
        )

        try:
            total_emotions = self._aggregate_emotions(emotions_data=data)
            average_emotions = self._get_average_emotions(total_emotions=total_emotions, result_count=len(data))
            return self._get_top_emotions(emotions=average_emotions, limit=limit)
        except Exception as e:
            raise AnalysisServiceException(f"Failed to process API response: {e}")
