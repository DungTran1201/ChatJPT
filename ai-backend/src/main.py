"""FastAPI application factory, global domain exception handlers, and middleware wiring."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.core.config import settings
from src.core.database import db_manager
from src.core.exceptions import DomainError
from src.core.telemetry_middleware import TelemetryMiddleware
from src.api.v1.router import api_router
from src.schemas.v1.health import HealthResponse


def create_app() -> FastAPI:
    application = FastAPI(
        title="ChatJPT Japanese Learning Backend API",
        description="Core backend server communicating with LLM integration engine for Japanese learning",
        version="1.0.0",
    )

    # Register central DomainError -> HTTP translation (decouples services from FastAPI)
    @application.exception_handler(DomainError)
    async def domain_error_handler(_request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.to_http_detail()},
            headers=exc.headers or None,
        )

    # Telemetry runs inside CORS so OPTIONS preflights aren't polluted
    application.add_middleware(TelemetryMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount API Routers
    application.include_router(api_router, prefix="/api/v1")

    @application.get("/")
    async def root():
        return {
            "service": "ai-backend",
            "status": "running",
            "docs_url": "/docs",
        }

    @application.get("/health", response_model=HealthResponse)
    async def health_check():
        db_ok = True
        try:
            db_manager.query_one("SELECT 1 AS ok")
        except Exception:
            db_ok = False
        return HealthResponse(
            status="healthy" if db_ok else "degraded",
            service="ai-backend",
            version="1.0.0",
            details={
                "service": "ai-backend",
                "database": "sqlite_connected" if db_ok else "sqlite_error",
            },
        )

    return application


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
