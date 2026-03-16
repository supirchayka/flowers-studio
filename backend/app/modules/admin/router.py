from fastapi import APIRouter

from app.modules.bookings.admin_router import router as bookings_router
from app.modules.schedule.admin_router import router as schedule_router
from app.modules.services.admin_router import router as services_router

router = APIRouter(prefix="/admin", tags=["admin"])
router.include_router(services_router)
router.include_router(schedule_router)
router.include_router(bookings_router)

