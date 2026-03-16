from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_admin
from app.db.models import BookingStatus, User
from app.db.session import get_db
from app.modules.bookings.schemas import BookingAdminRead, BookingStatusUpdate
from app.modules.bookings.service import booking_dashboard, list_admin_bookings, update_booking_status
from app.modules.notifications.service import NotificationService

router = APIRouter(prefix="/bookings", tags=["admin-bookings"])
notifier = NotificationService()


@router.get("", response_model=list[BookingAdminRead])
async def admin_get_bookings(
    _: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    status_filter: BookingStatus | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None),
) -> list[BookingAdminRead]:
    return await list_admin_bookings(session, date_from=date_from, date_to=date_to, status_filter=status_filter, search=search)


@router.patch("/{booking_id}/status", response_model=BookingAdminRead)
async def admin_patch_booking_status(
    booking_id: int,
    actor: Annotated[User, Depends(require_admin)],
    payload: BookingStatusUpdate,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> BookingAdminRead:
    return await update_booking_status(session, notifier, actor, booking_id, payload)


@router.get("/dashboard")
async def admin_get_dashboard(
    _: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, int]:
    return await booking_dashboard(session)
