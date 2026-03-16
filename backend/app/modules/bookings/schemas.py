from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.db.models import BookingStatus
from app.modules.auth.schemas import UserRead
from app.modules.services.schemas import ServiceRead


class SlotRead(BaseModel):
    start_at: datetime
    end_at: datetime
    label: str


class AvailabilityRead(BaseModel):
    date: date
    slots: list[SlotRead]


class BookingCreate(BaseModel):
    service_id: int
    start_at: datetime
    client_name: str = Field(min_length=2, max_length=255)
    client_phone: str = Field(min_length=5, max_length=64)
    client_comment: str | None = Field(default=None, max_length=2000)
    client_request_id: str | None = Field(default=None, max_length=255)


class BookingRead(BaseModel):
    id: int
    status: BookingStatus
    client_name: str
    client_phone: str
    client_comment: str | None
    start_at: datetime
    end_at: datetime
    service_name_snapshot: str
    service_price_snapshot: int
    service_currency_snapshot: str
    admin_note: str | None
    cancelled_at: datetime | None
    can_cancel: bool


class BookingAdminRead(BookingRead):
    service: ServiceRead
    user: UserRead


class BookingStatusUpdate(BaseModel):
    status: BookingStatus
    admin_note: str | None = Field(default=None, max_length=2000)

