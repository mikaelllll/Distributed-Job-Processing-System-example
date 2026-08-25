from typing import Any

import aio_pika
from aio_pika import DeliveryMode, ExchangeType, Message
from aio_pika.abc import AbstractChannel, AbstractRobustConnection

from app.config import get_settings

JOBS_EXCHANGE = "jobs"
JOBS_QUEUE = "jobs.execute"
CONTROL_EXCHANGE = "benchmark.control"
CONTROL_QUEUE = "benchmark.generate"
DEAD_EXCHANGE = "jobs.dead"
DEAD_QUEUE = "jobs.dead-letter"
RETRY_DELAYS = (1_000, 5_000, 30_000)


async def connect() -> AbstractRobustConnection:
    return await aio_pika.connect_robust(get_settings().rabbitmq_url)


async def declare_topology(channel: AbstractChannel) -> None:
    jobs = await channel.declare_exchange(JOBS_EXCHANGE, ExchangeType.DIRECT, durable=True)
    dead = await channel.declare_exchange(DEAD_EXCHANGE, ExchangeType.DIRECT, durable=True)
    control = await channel.declare_exchange(CONTROL_EXCHANGE, ExchangeType.DIRECT, durable=True)
    queue = await channel.declare_queue(JOBS_QUEUE, durable=True)
    await queue.bind(jobs, routing_key="execute")
    control_queue = await channel.declare_queue(CONTROL_QUEUE, durable=True)
    await control_queue.bind(control, routing_key="generate")
    dead_queue = await channel.declare_queue(DEAD_QUEUE, durable=True)
    await dead_queue.bind(dead, routing_key="dead")
    for attempt, delay in enumerate(RETRY_DELAYS, start=1):
        retry_queue = await channel.declare_queue(
            f"jobs.retry.{attempt}",
            durable=True,
            arguments={
                "x-message-ttl": delay,
                "x-dead-letter-exchange": JOBS_EXCHANGE,
                "x-dead-letter-routing-key": "execute",
            },
        )
        await retry_queue.bind(jobs, routing_key=f"retry.{attempt}")


def persistent_message(body: bytes, headers: dict[str, Any] | None = None) -> Message:
    return Message(body, delivery_mode=DeliveryMode.PERSISTENT, headers=headers or {})
