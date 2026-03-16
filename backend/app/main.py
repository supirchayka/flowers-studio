from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.db.session import init_db
from app.modules.admin.router import router as admin_router
from app.modules.auth.router import router as auth_router
from app.modules.bookings.router import router as bookings_router
from app.modules.services.router import router as services_router

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    yield


app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(services_router, prefix=settings.api_prefix)
app.include_router(bookings_router, prefix=settings.api_prefix)
app.include_router(admin_router, prefix=settings.api_prefix)


@app.get("/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
