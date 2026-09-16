import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.database import Base, engine
from app.error_handlers import register_exception_handlers
from app.logging_config import RequestLoggingMiddleware, setup_logging
from app.routes import health, incidents, services

settings = get_settings()
setup_logging(settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    logger.info("Application started: %s", settings.app_name)
    yield
    logger.info("Application stopped")


app = FastAPI(
    title=settings.app_name,
    description="A small incident and service-health API.",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(RequestLoggingMiddleware)
register_exception_handlers(app)

app.include_router(health.router)
app.include_router(services.router)
app.include_router(incidents.router)


@app.get("/", tags=["root"])
def root() -> dict[str, str]:
    return {"name": settings.app_name, "version": app.version}
