from typing import Any

import httpx

from app.core.config import Settings
from app.core.errors import InferenceServiceError


class InferenceClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def predict(self, image_bytes: bytes, content_type: str) -> dict[str, Any]:
        files = {"file": ("upload", image_bytes, content_type)}

        try:
            async with httpx.AsyncClient(
                base_url=self._settings.inference_base_url,
                timeout=self._settings.inference_timeout_seconds,
            ) as client:
                response = await client.post(self._settings.inference_predict_path, files=files)
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise InferenceServiceError() from exc

        return {
            "calories": float(payload.get("calories", 0)),
            "protein": float(payload.get("protein", 0)),
            "carbs": float(payload.get("carbs", 0)),
            "fat": float(payload.get("fat", 0)),
        }
