from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(slots=True, frozen=True)
class TimeInterval:
    start_at: datetime
    end_at: datetime


def overlaps(left: TimeInterval, right: TimeInterval) -> bool:
    return left.start_at < right.end_at and right.start_at < left.end_at


def interval_within_windows(interval: TimeInterval, windows: list[TimeInterval]) -> bool:
    return any(window.start_at <= interval.start_at and interval.end_at <= window.end_at for window in windows)


def build_available_slots(
    windows: list[TimeInterval],
    blocked: list[TimeInterval],
    occupied: list[TimeInterval],
    duration_minutes: int,
    step_minutes: int,
) -> list[TimeInterval]:
    slots: list[TimeInterval] = []
    step = timedelta(minutes=step_minutes)
    duration = timedelta(minutes=duration_minutes)
    seen: set[datetime] = set()

    for window in sorted(windows, key=lambda item: item.start_at):
        cursor = window.start_at
        latest_start = window.end_at - duration
        while cursor <= latest_start:
            candidate = TimeInterval(start_at=cursor, end_at=cursor + duration)
            if candidate.start_at not in seen:
                has_overlap = any(overlaps(candidate, item) for item in [*blocked, *occupied])
                if not has_overlap and interval_within_windows(candidate, windows):
                    slots.append(candidate)
                    seen.add(candidate.start_at)
            cursor += step

    return slots
