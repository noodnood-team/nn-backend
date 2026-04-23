from fastapi import APIRouter, Depends, File, UploadFile

from app.api.v1.routes.predict import get_prediction_service
from app.schemas.common import HealthResponse
from app.schemas.predict import PredictResponse
from app.services.prediction_service import PredictionService

router = APIRouter(tags=["sagemaker"])


@router.get("/ping", response_model=HealthResponse)
async def sagemaker_ping() -> HealthResponse:
    return HealthResponse()


@router.post("/invocations", response_model=PredictResponse)
async def sagemaker_invocations(
    file: UploadFile = File(...),
    prediction_service: PredictionService = Depends(get_prediction_service),
) -> PredictResponse:
    image_bytes = await file.read()
    prediction = await prediction_service.predict(
        image_bytes=image_bytes,
        content_type=file.content_type,
    )
    return PredictResponse(prediction=prediction)

