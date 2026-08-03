"""SideFit FastAPI 애플리케이션 생성 및 전역 설정 모듈."""

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import RequestLoggingMiddleware, configure_logging
from app.domains.auth.router import router as auth_router
from app.domains.projects.router import router as projects_router
from app.domains.users.router import router as users_router

settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(
    title="SideFit API",
    description="SideFit 백엔드 API 서버",
    version="0.1.0",
)

app.add_middleware(RequestLoggingMiddleware)
app.include_router(users_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")
register_exception_handlers(app)
