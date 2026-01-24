from __future__ import annotations

import asyncio
import logging

from app.config import load_settings
from app.di import build_container
from app.repositories.events import EventRepository
from app.repositories.uow import UnitOfWork


logger = logging.getLogger("event_closer")


async def main() -> None:
    settings = load_settings()
    container = build_container(settings)
    uow = UnitOfWork(container.sessionmaker)

    while True:
        try:
            async with uow:
                assert uow.session is not None
                events = EventRepository(uow.session)
                expired = await events.list_expired_open_events(limit=100)
                for event_id in expired:
                    await events.close_event(event_id)
        except Exception:
            logger.exception("worker loop failed")

        # Periodic polling is allowed; we do NOT create per-event timers.
        await asyncio.sleep(settings.event_closer_interval_seconds)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())

