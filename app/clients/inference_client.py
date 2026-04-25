from typing import Any
from fastapi import UploadFile
import httpx

from app.core.config import Settings
from app.core.errors import InferenceServiceError
from app.core.logging import get_logger

logger = get_logger(__name__)


class InferenceClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def predict(self, image_bytes: bytes, content_type: str, file: UploadFile) -> dict[str, Any]:
        files = {"image": (file.filename, image_bytes, content_type)}
        
        try:
            async with httpx.AsyncClient(
                base_url=self._settings.inference_base_url,
                timeout=self._settings.inference_timeout_seconds,
            ) as client:
                response = await client.post(
                    self._settings.inference_predict_path,
                    files=files,
                )
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPStatusError as exc:
            body = exc.response.text    
            logger.warning(
                "Inference request failed status=%s url=%s field=%s filename=%s bytes=%s body=%s",
                exc.response.status_code,
                str(exc.request.url),
                len(image_bytes),
                body[:8000] if body else "(empty)",
            )
            raise InferenceServiceError() from exc
        except httpx.HTTPError as exc:
            logger.warning("inference request error: %s", exc)
            raise InferenceServiceError() from exc
        except ValueError as exc:
            logger.warning("inference response was not valid JSON: %s", exc)
            raise InferenceServiceError() from exc
        
        
        return {
            "calories": float(payload.get("calories", 0)),
            "protein": float(payload.get("protein", 0)),
            "carbs": float(payload.get("carbs", 0)),
            "fat": float(payload.get("fat", 0)),
        }
