from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.exceptions import (
    AIServiceConfigError,
    AIServiceError,
    IncidentNotFoundError,
    ServiceNameAlreadyExistsError,
    ServiceNotFoundError,
)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(IncidentNotFoundError, handle_incident_not_found)
    app.add_exception_handler(ServiceNotFoundError, handle_service_not_found)
    app.add_exception_handler(ServiceNameAlreadyExistsError, handle_duplicate_service_name)
    app.add_exception_handler(AIServiceConfigError, handle_ai_service_config_error)
    app.add_exception_handler(AIServiceError, handle_ai_service_error)


async def handle_incident_not_found(_: Request, __: IncidentNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": "Incident not found"})


async def handle_service_not_found(_: Request, __: ServiceNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": "Service not found"})


async def handle_duplicate_service_name(
    _: Request,
    __: ServiceNameAlreadyExistsError,
) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": "Service name already exists"})


async def handle_ai_service_config_error(
    _: Request,
    exc: AIServiceConfigError,
) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={"detail": str(exc) or "AI service is not configured"},
    )


async def handle_ai_service_error(
    _: Request,
    exc: AIServiceError,
) -> JSONResponse:
    return JSONResponse(
        status_code=502,
        content={"detail": str(exc) or "AI incident analysis failed"},
    )
