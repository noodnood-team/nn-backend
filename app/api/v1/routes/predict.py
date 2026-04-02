from fastapi import APIRouter, Depends, File, UploadFile

from app.clients.inference_client import InferenceClient
from app.core.config import Settings, get_settings
from app.schemas.predict import PredictResponse
from app.services.image_service import ImageService
from app.services.prediction_service import PredictionService

router = APIRouter(tags=["prediction"])


def get_prediction_service(settings: Settings = Depends(get_settings)) -> PredictionService:
    image_service = ImageService(max_image_size_bytes=settings.max_image_size_bytes)
    inference_client = InferenceClient(settings=settings)
    return PredictionService(image_service=image_service, inference_client=inference_client)


@router.post("/predict", response_model=PredictResponse)
async def predict(
    file: UploadFile = File(...),
    prediction_service: PredictionService = Depends(get_prediction_service),
) -> PredictResponse:
    image_bytes = await file.read()
    prediction = await prediction_service.predict(
        image_bytes=image_bytes,
        content_type=file.content_type,
    )
    return PredictResponse(prediction=prediction)
