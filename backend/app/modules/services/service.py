from __future__ import annotations

import json
import re

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditLog, Service, User
from app.modules.services.schemas import ServiceCreate, ServiceUpdate


def slugify(name: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9а-яА-Я]+", "-", name.lower()).strip("-")
    return value or "service"


async def list_public_services(session: AsyncSession) -> list[Service]:
    result = await session.execute(
        select(Service)
        .where(Service.is_active.is_(True), Service.is_archived.is_(False))
        .order_by(Service.created_at.desc())
    )
    return list(result.scalars().all())


async def list_admin_services(session: AsyncSession) -> list[Service]:
    result = await session.execute(select(Service).order_by(Service.created_at.desc()))
    return list(result.scalars().all())


async def get_service_or_404(session: AsyncSession, service_id: int, include_archived: bool = False) -> Service:
    service = await session.get(Service, service_id)
    if service is None or (service.is_archived and not include_archived):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    return service


async def create_service(session: AsyncSession, actor: User, payload: ServiceCreate) -> Service:
    service = Service(
        name=payload.name,
        slug=await _generate_unique_slug(session, payload.name),
        description=payload.description,
        duration_minutes=payload.duration_minutes,
        price_minor=payload.price_minor,
        currency=payload.currency.upper(),
        is_active=payload.is_active,
    )
    session.add(service)
    await session.flush()
    await _log_action(session, actor, "service.created", "service", service.id, payload.model_dump())
    await session.commit()
    await session.refresh(service)
    return service


async def update_service(session: AsyncSession, actor: User, service: Service, payload: ServiceUpdate) -> Service:
    changes = payload.model_dump(exclude_none=True)
    for field, value in changes.items():
        if field == "currency":
            value = value.upper()
        setattr(service, field, value)

    if "name" in changes:
        service.slug = await _generate_unique_slug(session, changes["name"], current_id=service.id)

    await session.flush()
    await _log_action(session, actor, "service.updated", "service", service.id, changes)
    await session.commit()
    await session.refresh(service)
    return service


async def archive_service(session: AsyncSession, actor: User, service: Service) -> Service:
    service.is_archived = True
    service.is_active = False
    await session.flush()
    await _log_action(session, actor, "service.archived", "service", service.id, {})
    await session.commit()
    await session.refresh(service)
    return service


async def _generate_unique_slug(session: AsyncSession, name: str, current_id: int | None = None) -> str:
    base_slug = slugify(name)
    candidate = base_slug
    suffix = 1
    while True:
        result = await session.execute(select(Service).where(Service.slug == candidate))
        existing = result.scalar_one_or_none()
        if existing is None or existing.id == current_id:
            return candidate
        suffix += 1
        candidate = f"{base_slug}-{suffix}"


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

