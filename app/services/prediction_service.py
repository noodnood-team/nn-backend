from app.clients.inference_client import InferenceClient
from app.schemas.predict import NutritionPrediction
from app.services.image_service import ImageService
from fastapi import UploadFile

ESTIMATION_DISCLAIMER = (
    "This result is an estimate based on the uploaded image and may not be 100% accurate.",
    "The nutrition values are approximate and may vary depending on ingredients, portion size, and image quality."
)

class PredictionService:
    def __init__(self, image_service: ImageService, inference_client: InferenceClient) -> None:
        self._image_service = image_service
        self._inference_client = inference_client

    async def predict(
        self,
        image_bytes: bytes,
        content_type: str | None,
        file: UploadFile
    ) -> NutritionPrediction:
        prepared_image = self._image_service.preprocess(image_bytes)
        prediction = await self._inference_client.predict(
            image_bytes=prepared_image,
            content_type=content_type or "application/octet-stream",
            file=file,
        )
        return NutritionPrediction(**prediction)
