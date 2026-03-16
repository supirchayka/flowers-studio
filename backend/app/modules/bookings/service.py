from __future__ import annotations

import json
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.db.models import AuditLog, Booking, BookingStatus, Service, User
from app.modules.bookings.schemas import BookingAdminRead, BookingCreate, BookingRead, BookingStatusUpdate, SlotRead
from app.modules.bookings.slots import TimeInterval, interval_within_windows, overlaps, build_available_slots
from app.modules.notifications.service import NotificationService
from app.modules.schedule.service import get_daily_windows, get_overlapping_blocks
from app.modules.services.service import get_service_or_404

ACTIVE_BOOKING_STATUSES = [BookingStatus.NEW.value, BookingStatus.CONFIRMED.value, BookingStatus.COMPLETED.value]


def _tz() -> ZoneInfo:
    return ZoneInfo(get_settings().studio_timezone)


def _ensure_aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=_tz())
    return value


def _day_bounds(day: date) -> tuple[datetime, datetime]:
    tz = _tz()
    day_start = datetime.combine(day, time.min, tzinfo=tz)
    day_end = day_start + timedelta(days=1)
    return day_start, day_end


async def get_service_availability(session: AsyncSession, service_id: int, day: date) -> list[SlotRead]:
    service = await get_service_or_404(session, service_id)
    if not service.is_active or service.is_archived:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service unavailable")

    windows = await _build_working_windows(session, day)
    if not windows:
        return []

    day_start, day_end = _day_bounds(day)
    blocked = [
        TimeInterval(_ensure_aware(item.start_at), _ensure_aware(item.end_at))
        for item in await get_overlapping_blocks(session, day_start, day_end)
    ]
    occupied = [
        TimeInterval(_ensure_aware(item.start_at), _ensure_aware(item.end_at))
        for item in await _get_occupied_bookings(session, day_start, day_end)
    ]

    slots = build_available_slots(
        windows=windows,
        blocked=blocked,
        occupied=occupied,
        duration_minutes=service.duration_minutes,
        step_minutes=get_settings().slot_step_minutes,
    )

    return [
        SlotRead(start_at=slot.start_at, end_at=slot.end_at, label=slot.start_at.astimezone(_tz()).strftime("%H:%M"))
        for slot in slots
    ]


async def create_booking(
    session: AsyncSession,
    notifier: NotificationService,
    user: User,
    payload: BookingCreate,
) -> BookingRead:
    service = await get_service_or_404(session, payload.service_id)
    if not service.is_active or service.is_archived:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service unavailable")

    tz = _tz()
    start_at = payload.start_at.astimezone(tz) if payload.start_at.tzinfo else payload.start_at.replace(tzinfo=tz)
    end_at = start_at + timedelta(minutes=service.duration_minutes)
    if start_at <= datetime.now(tz=UTC):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Booking must be in the future")

    await _acquire_booking_lock(session, start_at)

    if payload.client_request_id:
        existing = await _find_existing_idempotent_booking(session, user.id, payload.client_request_id)
        if existing:
            return _serialize_booking(existing)

    await _ensure_slot_is_available(session, start_at, end_at)

    booking = Booking(
        user_id=user.id,
        service_id=service.id,
        status=BookingStatus.NEW.value,
        client_name=payload.client_name,
        client_phone=payload.client_phone,
        client_comment=payload.client_comment,
        client_request_id=payload.client_request_id,
        start_at=start_at,
        end_at=end_at,
        service_name_snapshot=service.name,
        service_price_snapshot=service.price_minor,
        service_currency_snapshot=service.currency,
    )
    session.add(booking)
    await session.flush()
    await _log_action(
        session,
        user,
        "booking.created",
        "booking",
        booking.id,
        {
            "service_id": service.id,
            "start_at": start_at.isoformat(),
            "end_at": end_at.isoformat(),
            "status": booking.status,
        },
    )
    await session.commit()

    await session.refresh(booking)
    await notifier.notify_booking_created(booking, user)
    return _serialize_booking(booking)


async def get_my_bookings(session: AsyncSession, user: User) -> list[BookingRead]:
    result = await session.execute(select(Booking).where(Booking.user_id == user.id).order_by(Booking.start_at.desc()))
    return [_serialize_booking(booking) for booking in result.scalars().all()]


async def get_my_booking_or_404(session: AsyncSession, user: User, booking_id: int) -> Booking:
    result = await session.execute(select(Booking).where(and_(Booking.id == booking_id, Booking.user_id == user.id)))
    booking = result.scalar_one_or_none()
    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    return booking


async def cancel_booking(session: AsyncSession, notifier: NotificationService, user: User, booking_id: int) -> BookingRead:
    booking = await get_my_booking_or_404(session, user, booking_id)
    if booking.status == BookingStatus.CANCELLED.value:
        return _serialize_booking(booking)
    booking_start_at = _ensure_aware(booking.start_at)
    assert booking_start_at is not None
    if booking_start_at <= datetime.now(tz=UTC):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Booking already started")

    booking.status = BookingStatus.CANCELLED.value
    booking.cancelled_at = datetime.now(tz=UTC)
    await session.flush()
    await _log_action(session, user, "booking.cancelled", "booking", booking.id, {"cancelled_at": booking.cancelled_at.isoformat()})
    await session.commit()

    await session.refresh(booking)
    await notifier.notify_booking_cancelled(booking, user)
    return _serialize_booking(booking)


async def list_admin_bookings(
    session: AsyncSession,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    status_filter: BookingStatus | None = None,
    search: str | None = None,
) -> list[BookingAdminRead]:
    query = select(Booking).options(selectinload(Booking.service), selectinload(Booking.user)).order_by(Booking.start_at.desc())
    if date_from:
        query = query.where(Booking.end_at >= date_from)
    if date_to:
        query = query.where(Booking.start_at <= date_to)
    if status_filter:
        query = query.where(Booking.status == status_filter.value)
    if search:
        term = f"%{search.lower()}%"
        query = query.where(
            or_(
                func.lower(Booking.client_name).like(term),
                func.lower(Booking.client_phone).like(term),
                func.lower(Booking.client_comment).like(term),
            )
        )

    result = await session.execute(query)
    return [_serialize_admin_booking(booking) for booking in result.scalars().unique().all()]


async def update_booking_status(
    session: AsyncSession,
    notifier: NotificationService,
    actor: User,
    booking_id: int,
    payload: BookingStatusUpdate,
) -> BookingAdminRead:
    result = await session.execute(
        select(Booking)
        .where(Booking.id == booking_id)
        .options(selectinload(Booking.service), selectinload(Booking.user))
    )
    booking = result.scalar_one_or_none()
    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    booking.status = payload.status.value
    booking.admin_note = payload.admin_note
    if payload.status == BookingStatus.CANCELLED:
        booking.cancelled_at = datetime.now(tz=UTC)
    await session.flush()
    await _log_action(
        session,
        actor,
        "booking.status.updated",
        "booking",
        booking.id,
        {"status": payload.status.value, "admin_note": payload.admin_note},
    )
    await session.commit()

    await session.refresh(booking)
    await notifier.notify_status_changed(booking, booking.user)
    return _serialize_admin_booking(booking)


async def booking_dashboard(session: AsyncSession) -> dict[str, int]:
    now = datetime.now(tz=UTC)
    result = await session.execute(
        select(Booking.status, func.count(Booking.id))
        .where(Booking.end_at >= now)
        .group_by(Booking.status)
    )
    data = {status_value: count for status_value, count in result.all()}
    return {
        "upcoming": sum(data.values()),
        "new": data.get(BookingStatus.NEW.value, 0),
        "confirmed": data.get(BookingStatus.CONFIRMED.value, 0),
        "cancelled": data.get(BookingStatus.CANCELLED.value, 0),
    }


async def _build_working_windows(session: AsyncSession, day: date) -> list[TimeInterval]:
    tz = _tz()
    windows: list[TimeInterval] = []
    for rule in await get_daily_windows(session, day):
        windows.append(
            TimeInterval(
                start_at=datetime.combine(day, rule.start_time, tzinfo=tz),
                end_at=datetime.combine(day, rule.end_time, tzinfo=tz),
            )
        )
    return windows


async def _get_occupied_bookings(session: AsyncSession, start_at: datetime, end_at: datetime) -> list[Booking]:
    result = await session.execute(
        select(Booking)
        .where(
            and_(
                Booking.status.in_(ACTIVE_BOOKING_STATUSES),
                Booking.start_at < end_at,
                Booking.end_at > start_at,
            )
        )
        .order_by(Booking.start_at)
    )
    return list(result.scalars().all())


async def _acquire_booking_lock(session: AsyncSession, start_at: datetime) -> None:
    if session.bind is None or session.bind.dialect.name != "postgresql":
        return

    lock_key = int(start_at.strftime("%Y%m%d"))
    await session.execute(text("SELECT pg_advisory_xact_lock(:lock_key)"), {"lock_key": lock_key})


async def _ensure_slot_is_available(session: AsyncSession, start_at: datetime, end_at: datetime) -> None:
    day = start_at.astimezone(_tz()).date()
    windows = await _build_working_windows(session, day)
    candidate = TimeInterval(start_at, end_at)
    if not windows or not interval_within_windows(candidate, windows):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slot is outside working hours")

    blocked = [
        TimeInterval(_ensure_aware(item.start_at), _ensure_aware(item.end_at))
        for item in await get_overlapping_blocks(session, start_at, end_at)
    ]
    occupied = [
        TimeInterval(_ensure_aware(item.start_at), _ensure_aware(item.end_at))
        for item in await _get_occupied_bookings(session, start_at, end_at)
    ]
    if any(overlaps(candidate, item) for item in [*blocked, *occupied]):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slot is no longer available")


async def _find_existing_idempotent_booking(session: AsyncSession, user_id: int, client_request_id: str) -> Booking | None:
    result = await session.execute(select(Booking).where(and_(Booking.user_id == user_id, Booking.client_request_id == client_request_id)))
    return result.scalar_one_or_none()


def _serialize_booking(booking: Booking) -> BookingRead:
    booking_start_at = _ensure_aware(booking.start_at)
    booking_end_at = _ensure_aware(booking.end_at)
    cancelled_at = _ensure_aware(booking.cancelled_at)
    assert booking_start_at is not None
    assert booking_end_at is not None
    can_cancel = booking.status != BookingStatus.CANCELLED.value and booking_start_at > datetime.now(tz=UTC)
    return BookingRead(
        id=booking.id,
        status=BookingStatus(booking.status),
        client_name=booking.client_name,
        client_phone=booking.client_phone,
        client_comment=booking.client_comment,
        start_at=booking_start_at,
        end_at=booking_end_at,
        service_name_snapshot=booking.service_name_snapshot,
        service_price_snapshot=booking.service_price_snapshot,
        service_currency_snapshot=booking.service_currency_snapshot,
        admin_note=booking.admin_note,
        cancelled_at=cancelled_at,
        can_cancel=can_cancel,
    )


def _serialize_admin_booking(booking: Booking) -> BookingAdminRead:
    return BookingAdminRead(
        **_serialize_booking(booking).model_dump(),
        service=booking.service,
        user=booking.user,
    )


async def _log_action(
    session: AsyncSession,
    actor: User | None,
    action: str,
    entity_type: str,
    entity_id: int | str,
    payload: dict,
) -> None:
    session.add(
        AuditLog(
            actor_user_id=actor.id if actor else None,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            payload_json=json.dumps(payload, ensure_ascii=False, default=str),
        )
    )
