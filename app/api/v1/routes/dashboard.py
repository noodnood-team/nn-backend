from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import RECORD_TTL, SUMMARY_TTL, cache_get, cache_set
from app.core.config import Settings, get_settings
from app.db.models import PredictionOutcome
from app.db.session import get_db
from app.schemas.dashboard import (
    DashboardSummaryResponse,
    PredictionRecordItem,
    PredictionRecordListResponse,
)
from app.services.dashboard import DashboardService

router = APIRouter(tags=["dashboard"])

# Cache key prefixes – used here and imported by predict.py for invalidation.
DASHBOARD_LIST_PREFIX = "dash:list:"
DASHBOARD_DETAIL_PREFIX = "dash:detail:"
DASHBOARD_SUMMARY_PREFIX = "dash:summary:"


def get_dashboard_service() -> DashboardService:
    return DashboardService()


async def verify_dashboard_access(
    settings: Settings = Depends(get_settings),
    x_dashboard_key: str | None = Header(default=None, alias="X-Dashboard-Key"),
) -> None:
    key = settings.dashboard_api_key
    if key and x_dashboard_key != key:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Dashboard-Key")


@router.get(
    "/dashboard/predictions",
    response_model=PredictionRecordListResponse,
    dependencies=[Depends(verify_dashboard_access)],
)
async def list_predictions(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    outcome: PredictionOutcome | None = Query(default=None),
    ok: bool | None = Query(default=None),
    created_after: datetime | None = Query(default=None),
    created_before: datetime | None = Query(default=None),
    session: AsyncSession = Depends(get_db),
    service: DashboardService = Depends(get_dashboard_service),
) -> PredictionRecordListResponse:
    cache_key = (
        f"{DASHBOARD_LIST_PREFIX}{limit}:{offset}:{outcome}:{ok}"
        f":{created_after}:{created_before}"
    )

    cached = await cache_get(cache_key)
    if cached is not None:
        return PredictionRecordListResponse(**cached)

    result = await service.list_records(
        session,
        limit=limit,
        offset=offset,
        outcome=outcome,
        ok=ok,
        created_after=created_after,
        created_before=created_before,
    )
    await cache_set(cache_key, result.model_dump(mode="json"), ttl=SUMMARY_TTL)
    return result


@router.get(
    "/dashboard/predictions/{record_id}",
    response_model=PredictionRecordItem,
    dependencies=[Depends(verify_dashboard_access)],
)
async def get_prediction(
    record_id: int,
    session: AsyncSession = Depends(get_db),
    service: DashboardService = Depends(get_dashboard_service),
) -> PredictionRecordItem:
    cache_key = f"{DASHBOARD_DETAIL_PREFIX}{record_id}"

    cached = await cache_get(cache_key)
    if cached is not None:
        return PredictionRecordItem(**cached)

    item = await service.get_record(session, record_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Prediction record not found")

    await cache_set(cache_key, item.model_dump(mode="json"), ttl=RECORD_TTL)
    return item


@router.get(
    "/dashboard/summary",
    response_model=DashboardSummaryResponse,
    dependencies=[Depends(verify_dashboard_access)],
)
async def dashboard_summary(
    start: datetime | None = Query(
        default=None,
        description="Range start (UTC), inclusive. Defaults to 24 hours before end.",
    ),
    end: datetime | None = Query(
        default=None,
        description="Range end (UTC), inclusive. Defaults to current UTC time.",
    ),
    session: AsyncSession = Depends(get_db),
    service: DashboardService = Depends(get_dashboard_service),
) -> DashboardSummaryResponse:
    end_dt = end if end is not None else datetime.now(timezone.utc)
    if end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=timezone.utc)
    start_dt = start if start is not None else end_dt - timedelta(days=1)
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=timezone.utc)
    if start_dt > end_dt:
        raise HTTPException(
            status_code=422,
            detail="start must be less than or equal to end",
        )

    cache_key = f"{DASHBOARD_SUMMARY_PREFIX}{start_dt.isoformat()}:{end_dt.isoformat()}"

    cached = await cache_get(cache_key)
    if cached is not None:
        return DashboardSummaryResponse(**cached)

    result = await service.summarize_records(session, range_start=start_dt, range_end=end_dt)
    await cache_set(cache_key, result.model_dump(mode="json"), ttl=SUMMARY_TTL)
    return result
