from collections import defaultdict

from api.models import AnalysisRequest, Emotion
from api.services.endpoint_requester import EndpointRequester


class AnalysisService:
    def __init__(self, base_url: str, endpoint_requester: EndpointRequester):
        self.base_url = base_url
        self.endpoint_requester = endpoint_requester

    @staticmethod
    def _aggregate_emotions(emotions_data: list[dict]):
        total_emotions = defaultdict(
            lambda: {
                "total": 0,
                "max_track": {
                    "track_id": None,
                    "percentage": 0
                }
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
        average_emotions = [
            Emotion(
                name=emotion,
                percentage=round(info["total"] / result_count, 2),
                track_id=track_id
            )
            for emotion, info
            in total_emotions.items()
            if (track_id := info["max_track"]["track_id"]) is not None
        ]

        return average_emotions

    @staticmethod
    def _get_top_emotions(emotions: list[Emotion], limit: int) -> list[Emotion]:
        top_emotions = sorted(emotions, key=lambda e: e.percentage, reverse=True)[:limit]

        return top_emotions

    async def get_top_emotions(self, analysis_requests: list[AnalysisRequest], limit: int = 5):
        url = f"{self.base_url}/emotional-profile"

        data = await self.endpoint_requester.post(
            url=url,
            json=[item.model_dump() for item in analysis_requests],
            timeout=None
        )

        total_emotions = self._aggregate_emotions(emotions_data=data)
        average_emotions = self._get_average_emotions(total_emotions=total_emotions, result_count=len(data))
        top_emotions = self._get_top_emotions(emotions=average_emotions, limit=limit)

        return top_emotions
