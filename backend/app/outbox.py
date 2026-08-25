import asyncio
import json
from datetime import UTC, datetime

import structlog
from sqlalchemy import select

from app.database import SessionFactory
from app.logging import configure_logging
from app.messaging import CONTROL_EXCHANGE, connect, declare_topology, persistent_message
from app.models import OutboxEvent

log = structlog.get_logger()


async def run() -> None:
    configure_logging()
    connection = await connect()
    async with connection:
        channel = await connection.channel(publisher_confirms=True)
        await declare_topology(channel)
        exchange = await channel.get_exchange(CONTROL_EXCHANGE)
        while True:
            async with SessionFactory() as session:
                query = (
                    select(OutboxEvent)
                    .where(OutboxEvent.published_at.is_(None))
                    .order_by(OutboxEvent.created_at)
                    .limit(100)
                    .with_for_update(skip_locked=True)
                )
                events = list(await session.scalars(query))
                for event in events:
                    await exchange.publish(
                        persistent_message(json.dumps(event.payload).encode()),
                        routing_key="generate",
                    )
                    event.published_at = datetime.now(UTC)
                await session.commit()
            if not events:
                await asyncio.sleep(0.5)


if __name__ == "__main__":
    asyncio.run(run())
