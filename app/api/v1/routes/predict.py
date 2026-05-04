import random

from fastapi import APIRouter, Depends, File, UploadFile

from app.clients.inference_client import InferenceClient
from app.core.config import Settings, get_settings
from app.schemas.predict import PredictResponse
from app.services.food_validation_service import NON_FOOD_IMAGE_MESSAGES, FoodValidationService
from app.services.image_service import ImageService
from app.services.openai_service import OpenAIService
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


def get_openai_service(settings: Settings = Depends(get_settings)) -> OpenAIService:
    return OpenAIService(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        timeout=settings.openai_timeout_seconds,
    )


@router.post("/predict", response_model=PredictResponse)
async def predict(
    file: UploadFile = File(...),
    image_service: ImageService = Depends(get_image_service),
    food_validation: FoodValidationService = Depends(get_food_validation_service),
    prediction_service: PredictionService = Depends(get_prediction_service),
    openai_service: OpenAIService = Depends(get_openai_service),
) -> PredictResponse:
    image_bytes = await file.read()

    image_service.validate(image_bytes=image_bytes, content_type=file.content_type)

    # Validate if the image is a food image
    food_result = await food_validation.validate(image_bytes, file.content_type)
    if not food_result.valid:
        return PredictResponse(ok=False, message=random.choice(NON_FOOD_IMAGE_MESSAGES))

    # Predict the nutrition of the image
    nutrition = await prediction_service.predict(image_bytes, file.content_type, file=file)

    # Generate a message from the nutrition
    message = await openai_service.generate_message(nutrition)
    if message is None:
        message = random.choice(ESTIMATION_DISCLAIMER)

    return PredictResponse(ok=True, prediction=nutrition, message=message)
