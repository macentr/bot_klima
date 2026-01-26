"""Admin service for statistics and broadcasts."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import NamedTuple

from sqlalchemy import select, func, and_, extract
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.db.models import UserModel, RoomModel, EventModel


class MonthlyStats(NamedTuple):
    """Monthly statistics."""
    total_users: int
    active_users: int  # Users with activity in the month
    total_rooms: int
    total_events: int
    events_by_type: dict[str, int]


class AdminService:
    """Service for admin operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_monthly_stats(self, year: int, month: int) -> MonthlyStats:
        """Get statistics for a specific month."""
        # Get month date range
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        # Total users (all time)
        total_users_result = await self.session.execute(select(func.count(UserModel.id)))
        total_users = total_users_result.scalar() or 0
        
        # Active users (with events in the month)
        active_users_result = await self.session.execute(
            select(func.count(func.distinct(EventModel.creator_id)))
            .where(
                and_(
                    EventModel.created_at >= start_date,
                    EventModel.created_at < end_date
                )
            )
        )
        active_users = active_users_result.scalar() or 0
        
        # Total rooms created in the month
        total_rooms_result = await self.session.execute(
            select(func.count(RoomModel.id))
        )
        total_rooms = total_rooms_result.scalar() or 0
        
        # Total events in the month
        total_events_result = await self.session.execute(
            select(func.count(EventModel.id))
            .where(
                and_(
                    EventModel.created_at >= start_date,
                    EventModel.created_at < end_date
                )
            )
        )
        total_events = total_events_result.scalar() or 0
        
        # Events by type in the month
        events_by_type_result = await self.session.execute(
            select(EventModel.type, func.count(EventModel.id))
            .where(
                and_(
                    EventModel.created_at >= start_date,
                    EventModel.created_at < end_date
                )
            )
            .group_by(EventModel.type)
        )
        events_by_type = {row[0]: row[1] for row in events_by_type_result}
        
        return MonthlyStats(
            total_users=total_users,
            active_users=active_users,
            total_rooms=total_rooms,
            total_events=total_events,
            events_by_type=events_by_type,
        )
    
    async def get_all_user_ids(self) -> list[int]:
        """Get all user IDs for broadcast."""
        result = await self.session.execute(select(UserModel.id))
        return [row[0] for row in result]
