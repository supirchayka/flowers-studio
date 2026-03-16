from __future__ import annotations

import json
from datetime import date, datetime

from fastapi import HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditLog, BlockedInterval, User, WeeklyScheduleRule
from app.modules.schedule.schemas import (
    BlockedIntervalCreate,
    BlockedIntervalUpdate,
    ScheduleRuleCreate,
    ScheduleRuleUpdate,
)


async def list_schedule_rules(session: AsyncSession) -> list[WeeklyScheduleRule]:
    result = await session.execute(select(WeeklyScheduleRule).order_by(WeeklyScheduleRule.weekday, WeeklyScheduleRule.start_time))
    return list(result.scalars().all())


async def create_schedule_rule(session: AsyncSession, actor: User, payload: ScheduleRuleCreate) -> WeeklyScheduleRule:
    rule = WeeklyScheduleRule(**payload.model_dump())
    session.add(rule)
    await session.flush()
    await _log_action(session, actor, "schedule.rule.created", "weekly_schedule_rule", rule.id, payload.model_dump(mode="json"))
    await session.commit()
    await session.refresh(rule)
    return rule


async def update_schedule_rule(
    session: AsyncSession,
    actor: User,
    rule_id: int,
    payload: ScheduleRuleUpdate,
) -> WeeklyScheduleRule:
    rule = await session.get(WeeklyScheduleRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule rule not found")

    changes = payload.model_dump(exclude_none=True)
    for field, value in changes.items():
        setattr(rule, field, value)
    if rule.end_time <= rule.start_time:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid schedule interval")

    await session.flush()
    await _log_action(session, actor, "schedule.rule.updated", "weekly_schedule_rule", rule.id, changes)
    await session.commit()
    await session.refresh(rule)
    return rule


async def delete_schedule_rule(session: AsyncSession, actor: User, rule_id: int) -> None:
    rule = await session.get(WeeklyScheduleRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule rule not found")

    await session.delete(rule)
    await _log_action(session, actor, "schedule.rule.deleted", "weekly_schedule_rule", rule_id, {})
    await session.commit()


async def list_blocked_intervals(session: AsyncSession, from_dt: datetime | None = None, to_dt: datetime | None = None) -> list[BlockedInterval]:
    query = select(BlockedInterval).order_by(BlockedInterval.start_at)
    if from_dt is not None:
        query = query.where(BlockedInterval.end_at > from_dt)
    if to_dt is not None:
        query = query.where(BlockedInterval.start_at < to_dt)
    result = await session.execute(query)
    return list(result.scalars().all())


async def create_blocked_interval(session: AsyncSession, actor: User, payload: BlockedIntervalCreate) -> BlockedInterval:
    interval = BlockedInterval(**payload.model_dump())
    session.add(interval)
    await session.flush()
    await _log_action(session, actor, "schedule.block.created", "blocked_interval", interval.id, payload.model_dump(mode="json"))
    await session.commit()
    await session.refresh(interval)
    return interval


async def update_blocked_interval(
    session: AsyncSession,
    actor: User,
    interval_id: int,
    payload: BlockedIntervalUpdate,
) -> BlockedInterval:
    interval = await session.get(BlockedInterval, interval_id)
    if interval is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blocked interval not found")

    changes = payload.model_dump(exclude_none=True)
    for field, value in changes.items():
        setattr(interval, field, value)

    if interval.end_at <= interval.start_at:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid blocked interval")

    await session.flush()
    await _log_action(session, actor, "schedule.block.updated", "blocked_interval", interval.id, changes)
    await session.commit()
    await session.refresh(interval)
    return interval


async def delete_blocked_interval(session: AsyncSession, actor: User, interval_id: int) -> None:
    interval = await session.get(BlockedInterval, interval_id)
    if interval is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blocked interval not found")

    await session.delete(interval)
    await _log_action(session, actor, "schedule.block.deleted", "blocked_interval", interval_id, {})
    await session.commit()


async def get_daily_windows(session: AsyncSession, day: date) -> list[WeeklyScheduleRule]:
    result = await session.execute(
        select(WeeklyScheduleRule)
        .where(and_(WeeklyScheduleRule.weekday == day.weekday(), WeeklyScheduleRule.is_active.is_(True)))
        .order_by(WeeklyScheduleRule.start_time)
    )
    return list(result.scalars().all())


async def get_overlapping_blocks(session: AsyncSession, from_dt: datetime, to_dt: datetime) -> list[BlockedInterval]:
    result = await session.execute(
        select(BlockedInterval)
        .where(and_(BlockedInterval.start_at < to_dt, BlockedInterval.end_at > from_dt))
        .order_by(BlockedInterval.start_at)
    )
    return list(result.scalars().all())


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

