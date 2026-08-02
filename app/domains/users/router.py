from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domains.users.schemas import UserResponse
from app.domains.users.service import UserService


router = APIRouter(
    prefix="/users",
    tags=["사용자"],
)
