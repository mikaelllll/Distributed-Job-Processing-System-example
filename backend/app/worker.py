import asyncio
import hashlib
import json
import os
import random
import socket
import time
import uuid
from contextlib import suppress
from typing import Any

import structlog
from aio_pika.abc import AbstractChannel, AbstractIncomingMessage

from app.config import get_settings
from app.database import SessionFactory
from app.logging import configure_logging
from app.messaging import (
    DEAD_EXCHANGE,
    JOBS_EXCHANGE,
    JOBS_QUEUE,
    RETRY_DELAYS,
    connect,
    declare_topology,
    persistent_message,
)
from app.models import ErrorSample
from app.redis_client import control_key, create_redis, metrics_key

log = structlog.get_logger()
WORKER_ID = f"{socket.gethostname()}-{os.getpid()}"
LATENCY_BUCKETS_MS = (10, 25, 50, 100, 250, 500, 1_000, 5_000, 60_000)


async def heartbeat(redis) -> None:  # type: ignore[no-untyped-def]
    while True:
        await redis.set(f"worker:{WORKER_ID}:heartbeat", time.time(), ex=15)
        await asyncio.sleep(5)


async def execute(message: AbstractIncomingMessage, channel: AbstractChannel, redis: Any) -> None:
    job = json.loads(message.body)
    run_id = job["run_id"]
    key = metrics_key(run_id)
    attempt = int(job["attempt"])
    started = time.perf_counter()
    async with message.process(ignore_processed=True):
        if await redis.get(control_key(run_id)) == "cancelled":
            await redis.hincrby(key, "cancelled", 1)
            return
        if attempt:
            await redis.hincrby(key, "retrying", -1)
        else:
            await redis.hincrby(key, "queued", -1)
        await redis.hincrby(key, "running", 1)
        await redis.hincrby(f"run:{run_id}:workers", WORKER_ID, 1)
        try:
            async with asyncio.timeout(max(5, int(job["duration_ms"]) / 1000 + 5)):
                await run_workload(job)
        except Exception as exc:
            await redis.hincrby(key, "running", -1)
            if attempt < int(job["max_retries"]):
                next_attempt = attempt + 1
                job["attempt"] = next_attempt
                retry_route = f"retry.{min(next_attempt, len(RETRY_DELAYS))}"
                exchange = await channel.get_exchange(JOBS_EXCHANGE)
                await exchange.publish(
                    persistent_message(json.dumps(job).encode()), routing_key=retry_route
                )
                await redis.hincrby(key, "retrying", 1)
                await redis.hincrby(key, "retries", 1)
            else:
                exchange = await channel.get_exchange(DEAD_EXCHANGE)
                await exchange.publish(persistent_message(message.body), routing_key="dead")
                await redis.hincrby(key, "failed", 1)
                await redis.hincrby(key, "dead_lettered", 1)
                await save_error(job, exc)
            return

        elapsed_ms = (time.perf_counter() - started) * 1_000
        queue_ms = max(0.0, (time.time() - float(job["submitted_at"])) * 1_000 - elapsed_ms)
        pipe = redis.pipeline()
        pipe.hincrby(key, "running", -1)
        pipe.hincrby(key, "completed", 1)
        pipe.hincrbyfloat(key, "processing_ms_total", elapsed_ms)
        pipe.hincrbyfloat(key, "queue_ms_total", queue_ms)
        pipe.hincrby(key, "latency_count", 1)
        for bucket in LATENCY_BUCKETS_MS:
            if elapsed_ms <= bucket:
                pipe.hincrby(f"run:{run_id}:latency_buckets", str(bucket), 1)
        await pipe.execute()


async def run_workload(job: dict[str, Any]) -> None:
    if random.random() < float(job["failure_probability"]):
        raise RuntimeError("Simulated workload failure")
    duration = int(job["duration_ms"]) / 1_000
    if job["workload"] == "cpu_light":
        await asyncio.to_thread(cpu_work, max(1, int(job["duration_ms"])))
    elif job["workload"] == "io_heavy":
        await asyncio.gather(*(asyncio.sleep(duration) for _ in range(4)))
    else:
        await asyncio.sleep(duration)


def cpu_work(rounds: int) -> None:
    value = b"distributed-job-platform"
    for _ in range(rounds * 200):
        value = hashlib.sha256(value).digest()


async def save_error(job: dict[str, Any], exc: Exception) -> None:
    async with SessionFactory() as session:
        session.add(
            ErrorSample(
                run_id=uuid.UUID(str(job["run_id"])),
                job_id=uuid.UUID(str(job["job_id"])),
                worker_id=WORKER_ID,
                attempt=int(job["attempt"]),
                error_type=type(exc).__name__,
                message=str(exc)[:500],
            )
        )
        await session.commit()


async def run() -> None:
    configure_logging()
    redis = create_redis()
    connection = await connect()
    heartbeat_task = asyncio.create_task(heartbeat(redis))
    try:
        async with connection:
            channel = await connection.channel(publisher_confirms=True)
            await channel.set_qos(prefetch_count=get_settings().worker_prefetch)
            await declare_topology(channel)
            queue = await channel.get_queue(JOBS_QUEUE)
            await queue.consume(lambda message: execute(message, channel, redis))
            await asyncio.Future()
    finally:
        heartbeat_task.cancel()
        with suppress(asyncio.CancelledError):
            await heartbeat_task
        await redis.aclose()


if __name__ == "__main__":
    asyncio.run(run())
