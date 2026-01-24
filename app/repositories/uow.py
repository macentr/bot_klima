from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class UnitOfWork:
    """
    Minimal Unit of Work wrapper.

    - Keeps transaction boundaries explicit
    - Avoids global state
    """

    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self._sessionmaker = sessionmaker
        self.session: AsyncSession | None = None

    async def __aenter__(self) -> "UnitOfWork":
        self.session = self._sessionmaker()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        assert self.session is not None
        try:
            if exc is None:
                await self.session.commit()
            else:
                await self.session.rollback()
        finally:
            await self.session.close()

