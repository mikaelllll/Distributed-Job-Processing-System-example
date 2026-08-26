import asyncio
import time
from datetime import UTC, datetime

from sqlalchemy import select

from app.config import get_settings
from app.database import SessionFactory
from app.logging import configure_logging
from app.models import BenchmarkRun, MetricSnapshot, RunStatus
from app.redis_client import create_redis, metrics_key
from app.worker import LATENCY_BUCKETS_MS


async def active_workers(redis) -> int:  # type: ignore[no-untyped-def]
    count = 0
    async for key in redis.scan_iter("worker:*:heartbeat"):
        if await redis.exists(key):
            count += 1
    return count


def percentile(buckets: dict[str, str], count: int, target: float) -> int:
    threshold = count * target
    for bucket in LATENCY_BUCKETS_MS:
        if int(buckets.get(str(bucket), 0)) >= threshold:
            return bucket
    return LATENCY_BUCKETS_MS[-1]


def reconcile_in_flight_metrics(numeric: dict[str, float]) -> tuple[int, int, int, int]:
    """Derive in-flight counts from lifecycle counters instead of timing-sensitive deltas."""
    submitted = int(numeric.get("submitted", 0))
    completed = int(numeric.get("completed", 0))
    failed = int(numeric.get("failed", 0))
    cancelled = int(numeric.get("cancelled", 0))
    running = max(0, int(numeric.get("running", 0)))
    retrying = max(0, int(numeric.get("retrying", 0)))
    terminal = completed + failed + cancelled
    queued = max(0, submitted - terminal - running - retrying)
    return queued, running, retrying, terminal


async def collect() -> None:
    settings = get_settings()
    redis = create_redis()
    try:
        while True:
            async with SessionFactory() as session:
                query = select(BenchmarkRun).where(
                    BenchmarkRun.status.in_([RunStatus.producing, RunStatus.running])
                )
                runs = list(await session.scalars(query))
                workers = await active_workers(redis)
                for run in runs:
                    key = metrics_key(str(run.id))
                    raw = await redis.hgetall(key)
                    if not raw:
                        continue
                    numeric = {k: float(v) for k, v in raw.items() if k != "started_at"}
                    started_at = float(raw.get("started_at", time.time()))
                    elapsed = max(0.001, time.time() - started_at)
                    completed = int(numeric.get("completed", 0))
                    failed = int(numeric.get("failed", 0))
                    latency_count = int(numeric.get("latency_count", 0))
                    buckets = await redis.hgetall(f"run:{run.id}:latency_buckets")
                    queued, running, retrying, terminal = reconcile_in_flight_metrics(numeric)
                    snapshot = {
                        **{k: int(v) if v.is_integer() else v for k, v in numeric.items()},
                        "queued": queued,
                        "running": running,
                        "retrying": retrying,
                        "active_workers": workers,
                        "elapsed_seconds": round(elapsed, 2),
                        "throughput": round((completed + failed) / elapsed, 2),
                        "average_processing_ms": round(
                            numeric.get("processing_ms_total", 0) / max(1, latency_count), 2
                        ),
                        "average_queue_ms": round(
                            numeric.get("queue_ms_total", 0) / max(1, latency_count), 2
                        ),
                        "p50_ms": percentile(buckets, latency_count, 0.50),
                        "p95_ms": percentile(buckets, latency_count, 0.95),
                        "p99_ms": percentile(buckets, latency_count, 0.99),
                    }
                    production_finished = bool(int(numeric.get("production_finished", 0)))
                    submitted = int(numeric.get("submitted", 0))
                    is_complete = (
                        production_finished
                        and submitted >= run.job_count
                        and terminal >= submitted
                        and running == 0
                        and retrying == 0
                    )
                    if is_complete:
                        snapshot.update(
                            queued=0,
                            running=0,
                            retrying=0,
                            stream_finished=1,
                        )
                        run.status = RunStatus.completed
                        run.completed_at = datetime.now(UTC)
                        run.final_metrics = snapshot
                    await redis.hset(
                        key,
                        mapping={k: v for k, v in snapshot.items() if isinstance(v, int | float)},
                    )
                    session.add(MetricSnapshot(run_id=run.id, metrics=snapshot))
                await session.commit()
            await asyncio.sleep(settings.metrics_flush_interval_seconds)
    finally:
        await redis.aclose()


if __name__ == "__main__":
    configure_logging()
    asyncio.run(collect())
