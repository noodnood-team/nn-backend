from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import PredictionOutcome, PredictionRecord
from app.schemas.dashboard import (
    DashboardSummaryResponse,
    NutritionAverages,
    OutcomeCount,
    PredictionRecordItem,
    PredictionRecordListResponse,
)


class DashboardService:
    async def list_records(
        self,
        session: AsyncSession,
        *,
        limit: int,
        offset: int,
        outcome: PredictionOutcome | None,
        ok: bool | None,
        created_after: datetime | None,
        created_before: datetime | None,
    ) -> PredictionRecordListResponse:
        filters = []
        if outcome is not None:
            filters.append(PredictionRecord.outcome == outcome)
        if ok is not None:
            filters.append(PredictionRecord.ok == ok)
        if created_after is not None:
            filters.append(PredictionRecord.created_at >= created_after)
        if created_before is not None:
            filters.append(PredictionRecord.created_at <= created_before)

        base = select(PredictionRecord)
        count_stmt = select(func.count()).select_from(PredictionRecord)
        if filters:
            for f in filters:
                base = base.where(f)
                count_stmt = count_stmt.where(f)

        base = base.order_by(PredictionRecord.created_at.desc()).limit(limit).offset(offset)

        total_result = await session.execute(count_stmt)
        total = int(total_result.scalar_one())

        rows = await session.execute(base)
        items = [PredictionRecordItem.model_validate(r) for r in rows.scalars().all()]

        return PredictionRecordListResponse(items=items, total=total, limit=limit, offset=offset)

    async def get_record(self, session: AsyncSession, record_id: int) -> PredictionRecordItem | None:
        stmt = select(PredictionRecord).where(PredictionRecord.id == record_id)
        row = await session.execute(stmt)
        rec = row.scalar_one_or_none()
        if rec is None:
            return None
        return PredictionRecordItem.model_validate(rec)

    async def summarize_records(
        self,
        session: AsyncSession,
        *,
        range_start: datetime,
        range_end: datetime,
    ) -> DashboardSummaryResponse:
        window = (PredictionRecord.created_at >= range_start) & (PredictionRecord.created_at <= range_end)

        total_stmt = select(func.count()).select_from(PredictionRecord).where(window)
        total = int((await session.execute(total_stmt)).scalar_one())

        by_outcome_stmt = (
            select(PredictionRecord.outcome, func.count(PredictionRecord.id))
            .where(window)
            .group_by(PredictionRecord.outcome)
        )
        rows = (await session.execute(by_outcome_stmt)).all()
        counts_map = {outcome: int(c) for outcome, c in rows}

        outcome_counts = [
            OutcomeCount(outcome=o, count=counts_map.get(o, 0)) for o in PredictionOutcome
        ]
        success_count = counts_map.get(PredictionOutcome.success, 0)

        nutrition_averages: NutritionAverages | None = None
        if success_count > 0:
            avg_stmt = select(
                func.avg(PredictionRecord.calories),
                func.avg(PredictionRecord.protein),
                func.avg(PredictionRecord.carbs),
                func.avg(PredictionRecord.fat),
            ).where(
                window,
                PredictionRecord.outcome == PredictionOutcome.success,
            )
            acal, apro, acar, afat = (await session.execute(avg_stmt)).one()
            if acal is not None:
                nutrition_averages = NutritionAverages(
                    avg_calories=float(acal),
                    avg_protein=float(apro or 0),
                    avg_carbs=float(acar or 0),
                    avg_fat=float(afat or 0),
                )

        return DashboardSummaryResponse(
            range_start=range_start,
            range_end=range_end,
            total_requests=total,
            success_count=success_count,
            outcome_counts=outcome_counts,
            nutrition_averages=nutrition_averages,
        )
