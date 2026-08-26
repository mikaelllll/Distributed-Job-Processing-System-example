import asyncio
import json
import time
import uuid
from datetime import UTC, datetime
from typing import Any

import structlog
from aio_pika.abc import AbstractChannel, AbstractIncomingMessage

from app.database import SessionFactory
from app.logging import configure_logging
from app.messaging import (
    CONTROL_QUEUE,
    JOBS_EXCHANGE,
    connect,
    declare_topology,
    persistent_message,
)
from app.models import BenchmarkRun, RunMode, RunStatus
from app.redis_client import control_key, create_redis, metrics_key

log = structlog.get_logger()


def job_id_for(run_id: uuid.UUID, index: int) -> str:
    """Return a stable identifier so resumed publication preserves handler idempotency keys."""
    return str(uuid.uuid5(run_id, str(index)))


async def generate(message: AbstractIncomingMessage, channel: AbstractChannel) -> None:
    try:
        run_id = uuid.UUID(json.loads(message.body)["run_id"])
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        log.warning("invalid_control_message")
        await message.reject(requeue=False)
        return

    async with message.process(requeue=True):
        async with SessionFactory() as session:
            run = await session.get(BenchmarkRun, run_id)
            if run is None or run.status not in {RunStatus.pending, RunStatus.producing}:
                return
            if run.status == RunStatus.pending:
                run.status = RunStatus.producing
                run.started_at = datetime.now(UTC)
                await session.commit()
            config: dict[str, Any] = {
                "job_count": run.job_count,
                "mode": run.mode.value,
                "producer_concurrency": run.producer_concurrency,
                "target_rate": run.target_rate,
                "workload": run.workload,
                "duration_ms": run.duration_ms,
                "failure_probability": run.failure_probability,
                "max_retries": run.max_retries,
            }

        redis = create_redis()
        try:
            key = metrics_key(str(run_id))
            if not await redis.exists(key):
                await redis.hset(
                    key,
                    mapping={
                        "requested": config["job_count"],
                        "submitted": 0,
                        "queued": 0,
                        "running": 0,
                        "completed": 0,
                        "failed": 0,
                        "retrying": 0,
                        "dead_lettered": 0,
                        "started_at": time.time(),
                    },
                )
                await redis.expire(key, 604_800)

            if config["mode"] == RunMode.simulation.value:
                await _simulate(str(run_id), config, redis)
            else:
                exchange = await channel.get_exchange(JOBS_EXCHANGE)
                batch_size = max(1, int(config["producer_concurrency"]))
                interval = batch_size / config["target_rate"] if config["target_rate"] else 0
                already_submitted = int(await redis.hget(key, "submitted") or 0)
                for start in range(already_submitted, config["job_count"], batch_size):
                    if await redis.get(control_key(str(run_id))) == "cancelled":
                        break
                    batch_started = time.monotonic()
                    count = min(batch_size, config["job_count"] - start)
                    messages = []
                    for offset in range(count):
                        job_index = start + offset
                        body = json.dumps(
                            {
                                "job_id": job_id_for(run_id, job_index),
                                "run_id": str(run_id),
                                "attempt": 0,
                                "workload": config["workload"],
                                "duration_ms": config["duration_ms"],
                                "failure_probability": config["failure_probability"],
                                "max_retries": config["max_retries"],
                                "submitted_at": time.time(),
                            }
                        ).encode()
                        messages.append(
                            exchange.publish(persistent_message(body), routing_key="execute")
                        )
                    await asyncio.gather(*messages)
                    await redis.hincrby(key, "submitted", count)
                    await redis.hincrby(key, "queued", count)
                    remaining = interval - (time.monotonic() - batch_started)
                    if remaining > 0:
                        await asyncio.sleep(remaining)
            await redis.hset(key, "production_finished", 1)
            async with SessionFactory() as session:
                run = await session.get(BenchmarkRun, run_id)
                if run and run.status == RunStatus.producing:
                    run.status = RunStatus.running
                    await session.commit()
        finally:
            await redis.aclose()


async def _simulate(run_id: str, config: dict[str, Any], redis: Any) -> None:
    total = int(config["job_count"])
    steps = min(100, max(10, total // 100_000))
    key = metrics_key(run_id)
    processed = int(await redis.hget(key, "submitted") or 0)
    remaining_total = total - processed
    remaining_steps = max(1, steps - int(steps * processed / total))
    for index in range(remaining_steps):
        if await redis.get(control_key(run_id)) == "cancelled":
            return
        completed = (
            total - processed
            if index == remaining_steps - 1
            else remaining_total // remaining_steps
        )
        processed += completed
        failures = int(completed * float(config["failure_probability"]))
        await redis.hincrby(key, "submitted", completed)
        await redis.hincrby(key, "completed", completed - failures)
        await redis.hincrby(key, "failed", failures)
        await asyncio.sleep(0.1)


async def run() -> None:
    configure_logging()
    connection = await connect()
    async with connection:
        channel = await connection.channel(publisher_confirms=True)
        await channel.set_qos(prefetch_count=1)
        await declare_topology(channel)
        queue = await channel.get_queue(CONTROL_QUEUE)
        await queue.consume(lambda message: generate(message, channel))
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(run())
