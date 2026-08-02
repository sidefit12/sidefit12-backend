from fastapi import APIRouter

router = APIRouter(
    prefix="/users",
    tags=["사용자"],
)
