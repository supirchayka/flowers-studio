from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.services.schemas import ServiceRead
from app.modules.services.service import get_service_or_404, list_public_services

router = APIRouter(prefix="/services", tags=["services"])


@router.get("", response_model=list[ServiceRead])
async def get_services(session: Annotated[AsyncSession, Depends(get_db)]) -> list[ServiceRead]:
    services = await list_public_services(session)
    return [ServiceRead.model_validate(service) for service in services]


@router.get("/{service_id}", response_model=ServiceRead)
async def get_service(service_id: int, session: Annotated[AsyncSession, Depends(get_db)]) -> ServiceRead:
    service = await get_service_or_404(session, service_id)
    return ServiceRead.model_validate(service)

