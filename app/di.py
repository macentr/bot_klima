from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.config import Settings
from app.repositories.db.session import create_engine, create_sessionmaker


@dataclass(frozen=True)
class Container:
    settings: Settings
    engine: AsyncEngine
    sessionmaker: async_sessionmaker[AsyncSession]


def build_container(settings: Settings) -> Container:
    engine = create_engine(settings.database_url)
    sessionmaker = create_sessionmaker(engine)
    return Container(settings=settings, engine=engine, sessionmaker=sessionmaker)

