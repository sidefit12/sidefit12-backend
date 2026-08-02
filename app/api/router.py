from fastapi import APIRouter
from app.domains.users.router import router as users_router


api_router = APIRouter(prefix="/api/v1")

api_router.include_router(users_router)