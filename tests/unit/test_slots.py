from datetime import datetime
from zoneinfo import ZoneInfo

from app.modules.bookings.slots import TimeInterval, build_available_slots


def test_build_available_slots_respects_blocks_and_existing_bookings():
    tz = ZoneInfo("Europe/Moscow")
    windows = [
        TimeInterval(
            start_at=datetime(2026, 3, 20, 10, 0, tzinfo=tz),
            end_at=datetime(2026, 3, 20, 16, 0, tzinfo=tz),
        )
    ]
    blocked = [
        TimeInterval(
            start_at=datetime(2026, 3, 20, 12, 0, tzinfo=tz),
            end_at=datetime(2026, 3, 20, 13, 0, tzinfo=tz),
        )
    ]
    occupied = [
        TimeInterval(
            start_at=datetime(2026, 3, 20, 14, 0, tzinfo=tz),
            end_at=datetime(2026, 3, 20, 15, 0, tzinfo=tz),
        )
    ]

    slots = build_available_slots(
        windows=windows,
        blocked=blocked,
        occupied=occupied,
        duration_minutes=60,
        step_minutes=30,
    )

    labels = [slot.start_at.strftime("%H:%M") for slot in slots]
    assert labels == ["10:00", "10:30", "11:00", "13:00", "15:00"]
