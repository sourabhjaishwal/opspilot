import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.error_handlers import register_exception_handlers
from app.logging_config import RequestLoggingMiddleware, setup_logging
from app.routes import auth, health, incidents, services
from app.services.service_service import start_service_health_monitor

settings = get_settings()
setup_logging(settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    task = start_service_health_monitor()
    logger.info("Application started: %s", settings.app_name)
    try:
        yield
    finally:
        task.cancel()
        logger.info("Application stopped")


app = FastAPI(
    title=settings.app_name,
    description="A small incident and service-health API.",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)
register_exception_handlers(app)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(services.router)
app.include_router(incidents.router)


@app.get("/", tags=["root"])
def root() -> dict[str, str]:
    return {"name": settings.app_name, "version": app.version}
