"""API v1 도메인 router를 조합하는 모듈."""

from fastapi import APIRouter

from app.domains.auth.router import router as auth_router
from app.domains.users.router import router as users_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(users_router)
api_router.include_router(auth_router)
