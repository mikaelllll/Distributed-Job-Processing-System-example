import asyncio
import json
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.database import get_session
from app.models import BenchmarkRun, OutboxEvent, RunStatus
from app.redis_client import control_key, create_redis, metrics_key
from app.schemas import BenchmarkCreate, BenchmarkDetail, BenchmarkRead, RunActionResponse

router = APIRouter(prefix="/runs", tags=["benchmark runs"])


@router.post("", response_model=BenchmarkRead, status_code=status.HTTP_201_CREATED)
async def create_run(
    payload: BenchmarkCreate, session: AsyncSession = Depends(get_session)
) -> BenchmarkRun:
    settings = get_settings()
    if payload.job_count > settings.public_max_jobs and payload.mode.value != "simulation":
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "Job count exceeds deployment limit"
        )
    run = BenchmarkRun(**payload.model_dump())
    session.add(run)
    await session.flush()
    session.add(OutboxEvent(topic="benchmark.generate", payload={"run_id": str(run.id)}))
    await session.commit()
    await session.refresh(run)
    return run


@router.get("", response_model=list[BenchmarkRead])
async def list_runs(
    limit: int = Query(default=25, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> list[BenchmarkRun]:
    result = await session.scalars(
        select(BenchmarkRun).order_by(BenchmarkRun.created_at.desc()).limit(limit)
    )
    return list(result)


@router.get("/{run_id}", response_model=BenchmarkDetail)
async def get_run(
    run_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> BenchmarkDetail:
    query = (
        select(BenchmarkRun)
        .options(selectinload(BenchmarkRun.snapshots))
        .where(BenchmarkRun.id == run_id)
    )
    run = await session.scalar(query)
    if run is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Benchmark run not found")
    data = BenchmarkRead.model_validate(run).model_dump()
    data["snapshots"] = [
        {"timestamp": snapshot.recorded_at.isoformat(), **snapshot.metrics}
        for snapshot in sorted(run.snapshots, key=lambda item: item.recorded_at)
    ]
    return BenchmarkDetail.model_validate(data)


@router.post("/{run_id}/cancel", response_model=RunActionResponse)
async def cancel_run(
    run_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> RunActionResponse:
    run = await session.get(BenchmarkRun, run_id)
    if run is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Benchmark run not found")
    if run.status in {RunStatus.completed, RunStatus.failed, RunStatus.cancelled}:
        raise HTTPException(status.HTTP_409_CONFLICT, "Run is already terminal")
    run.status = RunStatus.cancelled
    run.completed_at = datetime.now(UTC)
    redis = create_redis()
    try:
        await redis.set(control_key(str(run_id)), "cancelled", ex=86_400)
    finally:
        await redis.aclose()
    await session.commit()
    return RunActionResponse(id=run.id, status=run.status)


@router.get("/{run_id}/events")
async def stream_run(run_id: uuid.UUID, request: Request) -> StreamingResponse:
    redis = create_redis()

    async def events() -> AsyncIterator[str]:
        try:
            while not await request.is_disconnected():
                values = await redis.hgetall(metrics_key(str(run_id)))
                payload = {key: _number(value) for key, value in values.items()}
                payload["queued"] = payload.get("pending", payload.get("queued", 0))
                payload["timestamp"] = datetime.now(UTC).isoformat()
                yield f"event: metrics\ndata: {json.dumps(payload)}\n\n"
                if payload.get("stream_finished") == 1:
                    break
                await asyncio.sleep(1)
        finally:
            await redis.aclose()

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _number(value: str) -> int | float | str:
    try:
        number = float(value)
        return int(number) if number.is_integer() else number
    except ValueError:
        return value
