from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_admin
from app.db.models import User
from app.db.session import get_db
from app.modules.services.schemas import ServiceCreate, ServiceRead, ServiceUpdate
from app.modules.services.service import archive_service, create_service, get_service_or_404, list_admin_services, update_service

router = APIRouter(prefix="/services", tags=["admin-services"])


@router.get("", response_model=list[ServiceRead])
async def admin_get_services(
    _: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[ServiceRead]:
    services = await list_admin_services(session)
    return [ServiceRead.model_validate(service) for service in services]


@router.post("", response_model=ServiceRead, status_code=status.HTTP_201_CREATED)
async def admin_create_service(
    actor: Annotated[User, Depends(require_admin)],
    payload: ServiceCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ServiceRead:
    service = await create_service(session, actor, payload)
    return ServiceRead.model_validate(service)


@router.patch("/{service_id}", response_model=ServiceRead)
async def admin_update_service(
    service_id: int,
    actor: Annotated[User, Depends(require_admin)],
    payload: ServiceUpdate,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ServiceRead:
    service = await get_service_or_404(session, service_id, include_archived=True)
    updated = await update_service(session, actor, service, payload)
    return ServiceRead.model_validate(updated)


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_archive_service(
    service_id: int,
    actor: Annotated[User, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    service = await get_service_or_404(session, service_id, include_archived=True)
    await archive_service(session, actor, service)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
