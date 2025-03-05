from api.models import AnalysisRequest, Emotion
from api.services.endpoint_requester import EndpointRequester


class AnalysisService:
    def __init__(self, base_url: str, endpoint_requester: EndpointRequester):
        self.base_url = base_url
        self.endpoint_requester = endpoint_requester

    async def get_top_emotions(self, analysis_requests: list[AnalysisRequest], limit: int = 5):
        url = f"{self.base_url}/emotional-profile"

        data = await self.endpoint_requester.post(
            url=url,
            json=[item.model_dump() for item in analysis_requests],
            timeout=None
        )

        result_count = len(data)

        total_emotions = {}

        for entry in data:
            emotional_profile = entry["emotional_profile"]

            for emotion, percentage in emotional_profile.items():
                if emotion not in total_emotions:
                    total_emotions[emotion] = {
                        "total": percentage,
                        "max_track": {
                            "id": entry["id"],
                            "percentage": percentage
                        }
                    }
                else:
                    total_emotions[emotion]["total"] += percentage
                    if percentage > total_emotions[emotion]["max_track"]["percentage"]:
                        total_emotions[emotion]["max_track"] = {"id": entry["id"], "percentage": percentage}

        average_emotions = [
            Emotion(
                name=emotion,
                percentage=round(info["total"] / result_count, 2),
                track_id=info["max_track"]["id"]
            )
            for emotion, info
            in total_emotions.items()
        ]

        top_emotions = sorted(average_emotions, key=lambda e: e.percentage, reverse=True)[:limit]

        return top_emotions
