from __future__ import annotations

from app.db.models import PredictionOutcome
from app.schemas.predict import NutritionPrediction
from app.services.prediction_history_service import PredictionHistoryService


async def record_prediction_attempt(
    history: PredictionHistoryService,
    *,
    filename: str | None,
    content_type: str | None,
    outcome: PredictionOutcome,
    ok: bool,
    message: str | None = None,
    nutrition: NutritionPrediction | None = None,
    detail: str | None = None,
) -> int:
    """Persist one prediction row; forwards to `PredictionHistoryService.persist`."""
    return await history.persist(
        outcome=outcome,
        ok=ok,
        message=message,
        filename=filename,
        content_type=content_type,
        nutrition=nutrition,
        detail=detail,
    )
