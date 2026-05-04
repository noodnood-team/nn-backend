from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.models import PredictionOutcome, PredictionRecord
from app.schemas.predict import NutritionPrediction


class PredictionHistoryService:
    """Persists prediction attempts using a short-lived session so rows survive handler exceptions."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def persist(
        self,
        *,
        outcome: PredictionOutcome,
        ok: bool,
        message: str | None = None,
        filename: str | None = None,
        content_type: str | None = None,
        nutrition: NutritionPrediction | None = None,
        detail: str | None = None,
    ) -> int:
        now = datetime.now(timezone.utc)
        record = PredictionRecord(
            created_at=now,
            outcome=outcome,
            ok=ok,
            message=message,
            filename=filename,
            content_type=content_type,
            detail=detail,
            calories=nutrition.calories if nutrition else None,
            protein=nutrition.protein if nutrition else None,
            carbs=nutrition.carbs if nutrition else None,
            fat=nutrition.fat if nutrition else None,
        )
        async with self._session_factory() as session:
            session.add(record)
            await session.flush()
            record_id = record.id
            await session.commit()
        return record_id
