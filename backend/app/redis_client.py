from typing import Any

from redis.asyncio import Redis

from app.config import get_settings


def create_redis() -> Any:
    return Redis.from_url(get_settings().redis_url, decode_responses=True)


def metrics_key(run_id: str) -> str:
    return f"run:{run_id}:metrics"


def control_key(run_id: str) -> str:
    return f"run:{run_id}:control"


def latency_key(run_id: str) -> str:
    return f"run:{run_id}:latency_buckets"


def workers_key(run_id: str) -> str:
    return f"run:{run_id}:workers"
