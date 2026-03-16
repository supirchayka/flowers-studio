from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.models import User
from app.db.session import get_db
from app.modules.bookings.schemas import AvailabilityRead, BookingCreate, BookingRead
from app.modules.bookings.service import cancel_booking, create_booking, get_my_bookings, get_service_availability
from app.modules.notifications.service import NotificationService

router = APIRouter(tags=["bookings"])
notifier = NotificationService()


@router.get("/services/{service_id}/availability", response_model=AvailabilityRead)
async def get_availability(
    service_id: int,
    day: date,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> AvailabilityRead:
    slots = await get_service_availability(session, service_id, day)
    return AvailabilityRead(date=day, slots=slots)


@router.post("/bookings", response_model=BookingRead)
async def post_booking(
    payload: BookingCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> BookingRead:
    return await create_booking(session, notifier, current_user, payload)


@router.get("/bookings/me", response_model=list[BookingRead])
async def list_my_bookings(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[BookingRead]:
    return await get_my_bookings(session, current_user)


@router.post("/bookings/{booking_id}/cancel", response_model=BookingRead)
async def post_cancel_booking(
    booking_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> BookingRead:
    return await cancel_booking(session, notifier, current_user, booking_id)

