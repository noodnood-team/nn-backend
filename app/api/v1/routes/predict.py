import random

from fastapi import APIRouter, Depends, File, UploadFile

from app.clients.inference_client import InferenceClient
from app.core.config import Settings, get_settings
from app.core.errors import AppError, ImageValidationError, InferenceServiceError
from app.db.models import PredictionOutcome
from app.db.session import get_session_factory
from app.schemas.predict import PredictResponse
from app.services.food_validation_service import NON_FOOD_IMAGE_MESSAGES, FoodValidationService
from app.services.image_service import ImageService
from app.services.openai_service import OpenAIService
from app.services.helper_service import record_prediction_attempt
from app.services.prediction_history_service import PredictionHistoryService
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


def get_prediction_history_service() -> PredictionHistoryService:
    return PredictionHistoryService(get_session_factory())


@router.post("/predict", response_model=PredictResponse)
async def predict(
    file: UploadFile = File(...),
    image_service: ImageService = Depends(get_image_service),
    food_validation: FoodValidationService = Depends(get_food_validation_service),
    prediction_service: PredictionService = Depends(get_prediction_service),
    openai_service: OpenAIService = Depends(get_openai_service),
    history: PredictionHistoryService = Depends(get_prediction_history_service),
) -> PredictResponse:
    filename = file.filename
    content_type = file.content_type

    try:
        image_bytes = await file.read()

        image_service.validate(image_bytes=image_bytes, content_type=file.content_type)

        food_result = await food_validation.validate(image_bytes, file.content_type)
        if not food_result.valid:
            msg = random.choice(NON_FOOD_IMAGE_MESSAGES)
            await record_prediction_attempt(
                history,
                filename=filename,
                content_type=content_type,
                outcome=PredictionOutcome.rejected_non_food,
                ok=False,
                message=msg,
                detail=food_result.reason,
            )
            return PredictResponse(ok=False, message=msg)

        nutrition = await prediction_service.predict(image_bytes, file.content_type, file=file)

        message = await openai_service.generate_message(nutrition)
        if message is None:
            message = random.choice(ESTIMATION_DISCLAIMER)

        await record_prediction_attempt(
            history,
            filename=filename,
            content_type=content_type,
            outcome=PredictionOutcome.success,
            ok=True,
            message=message,
            nutrition=nutrition,
        )
        return PredictResponse(ok=True, prediction=nutrition, message=message)

    except ImageValidationError as exc:
        await record_prediction_attempt(
            history,
            filename=filename,
            content_type=content_type,
            outcome=PredictionOutcome.validation_error,
            ok=False,
            message=exc.message,
            detail=exc.code,
        )
        raise
    except InferenceServiceError as exc:
        await record_prediction_attempt(
            history,
            filename=filename,
            content_type=content_type,
            outcome=PredictionOutcome.inference_error,
            ok=False,
            message=exc.message,
            detail=exc.code,
        )
        raise
    except AppError as exc:
        await record_prediction_attempt(
            history,
            filename=filename,
            content_type=content_type,
            outcome=PredictionOutcome.validation_error,
            ok=False,
            message=exc.message,
            detail=exc.code,
        )
        raise
    except Exception as exc:
        await record_prediction_attempt(
            history,
            filename=filename,
            content_type=content_type,
            outcome=PredictionOutcome.internal_error,
            ok=False,
            message=None,
            detail=type(exc).__name__,
        )
        raise
