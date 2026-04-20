import random

from fastapi import APIRouter, Depends, File, UploadFile

from app.clients.inference_client import InferenceClient
from app.core.config import Settings, get_settings
from app.schemas.predict import PredictResponse
from app.services.food_validation_service import NON_FOOD_IMAGE_MESSAGES, FoodValidationService
from app.services.image_service import ImageService
from app.services.prediction_service import ESTIMATION_DISCLAIMER, PredictionService

router = APIRouter(tags=["prediction"])


def get_image_service(settings: Settings = Depends(get_settings)) -> ImageService:
    return ImageService(max_image_size_bytes=settings.max_image_size_bytes)


def get_food_validation_service(settings: Settings = Depends(get_settings)) -> FoodValidationService:
    return FoodValidationService(
        model_id=settings.food_clip_model_id,
        food_probability_threshold=settings.food_clip_threshold,
    )


def get_prediction_service(
    settings: Settings = Depends(get_settings),
    image_service: ImageService = Depends(get_image_service),
) -> PredictionService:
    return PredictionService(
        image_service=image_service,
        inference_client=InferenceClient(settings=settings),
    )


@router.post("/predict", response_model=PredictResponse)
async def predict(
    file: UploadFile = File(...),
    image_service: ImageService = Depends(get_image_service),
    food_validation: FoodValidationService = Depends(get_food_validation_service),
    prediction_service: PredictionService = Depends(get_prediction_service),
) -> PredictResponse:
    image_bytes = await file.read()

    image_service.validate(image_bytes=image_bytes, content_type=file.content_type)

    food_result = await food_validation.validate(image_bytes, file.content_type)
    if not food_result.valid:
        return PredictResponse(ok=False, message=random.choice(NON_FOOD_IMAGE_MESSAGES))

    nutrition = await prediction_service.predict(image_bytes, file.content_type)
    return PredictResponse(ok=True, prediction=nutrition, message=random.choice(ESTIMATION_DISCLAIMER))
