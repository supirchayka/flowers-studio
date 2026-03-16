from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_admin
from app.db.models import User
from app.db.session import get_db
from app.modules.schedule.schemas import (
    BlockedIntervalCreate,
    BlockedIntervalRead,
    BlockedIntervalUpdate,
    ScheduleRuleCreate,
    ScheduleRuleRead,
    ScheduleRuleUpdate,
)
from app.modules.schedule.service import (
    create_blocked_interval,
    create_schedule_rule,
    delete_blocked_interval,
    delete_schedule_rule,
    list_blocked_intervals,
    list_schedule_rules,
    update_blocked_interval,
    update_schedule_rule,
)

router = APIRouter(prefix="/schedule", tags=["admin-schedule"])


@router.get("/rules", response_model=list[ScheduleRuleRead])
async def admin_get_schedule_rules(
    _: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[ScheduleRuleRead]:
    rules = await list_schedule_rules(session)
    return [ScheduleRuleRead.model_validate(rule) for rule in rules]


@router.post("/rules", response_model=ScheduleRuleRead, status_code=status.HTTP_201_CREATED)
async def admin_create_schedule_rule(
    actor: Annotated[User, Depends(require_admin)],
    payload: ScheduleRuleCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ScheduleRuleRead:
    rule = await create_schedule_rule(session, actor, payload)
    return ScheduleRuleRead.model_validate(rule)


@router.patch("/rules/{rule_id}", response_model=ScheduleRuleRead)
async def admin_update_schedule_rule(
    rule_id: int,
    actor: Annotated[User, Depends(require_admin)],
    payload: ScheduleRuleUpdate,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ScheduleRuleRead:
    rule = await update_schedule_rule(session, actor, rule_id, payload)
    return ScheduleRuleRead.model_validate(rule)


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_schedule_rule(
    rule_id: int,
    actor: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    await delete_schedule_rule(session, actor, rule_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/blocked-intervals", response_model=list[BlockedIntervalRead])
async def admin_get_blocked_intervals(
    _: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
    from_dt: datetime | None = Query(default=None),
    to_dt: datetime | None = Query(default=None),
) -> list[BlockedIntervalRead]:
    intervals = await list_blocked_intervals(session, from_dt=from_dt, to_dt=to_dt)
    return [BlockedIntervalRead.model_validate(interval) for interval in intervals]


@router.post("/blocked-intervals", response_model=BlockedIntervalRead, status_code=status.HTTP_201_CREATED)
async def admin_create_blocked_interval(
    actor: Annotated[User, Depends(require_admin)],
    payload: BlockedIntervalCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> BlockedIntervalRead:
    interval = await create_blocked_interval(session, actor, payload)
    return BlockedIntervalRead.model_validate(interval)


@router.patch("/blocked-intervals/{interval_id}", response_model=BlockedIntervalRead)
async def admin_update_blocked_interval(
    interval_id: int,
    actor: Annotated[User, Depends(require_admin)],
    payload: BlockedIntervalUpdate,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> BlockedIntervalRead:
    interval = await update_blocked_interval(session, actor, interval_id, payload)
    return BlockedIntervalRead.model_validate(interval)


@router.delete("/blocked-intervals/{interval_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_blocked_interval(
    interval_id: int,
    actor: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    await delete_blocked_interval(session, actor, interval_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
