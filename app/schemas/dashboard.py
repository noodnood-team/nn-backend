from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.db.models import PredictionOutcome


class PredictionRecordItem(BaseModel):
    id: int
    created_at: datetime
    outcome: PredictionOutcome
    ok: bool
    message: str | None = None
    filename: str | None = None
    content_type: str | None = None
    calories: float | None = None
    protein: float | None = None
    carbs: float | None = None
    fat: float | None = None
    detail: str | None = None

    model_config = {"from_attributes": True}


class PredictionRecordListResponse(BaseModel):
    items: list[PredictionRecordItem]
    total: int
    limit: int = Field(ge=1, le=50)
    offset: int = Field(ge=0)


class OutcomeCount(BaseModel):
    outcome: PredictionOutcome
    count: int = Field(ge=0)


class NutritionAverages(BaseModel):
    avg_calories: float
    avg_protein: float
    avg_carbs: float
    avg_fat: float


class DashboardSummaryResponse(BaseModel):
    """Aggregates for prediction_records in [range_start, range_end] (inclusive, UTC)."""

    range_start: datetime
    range_end: datetime
    total_requests: int = Field(ge=0)
    success_count: int = Field(ge=0)
    outcome_counts: list[OutcomeCount]
    nutrition_averages: NutritionAverages | None = None
