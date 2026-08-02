from fastapi import FastAPI
from app.api.router import api_router

app = FastAPI(
    title="SideFit API",
    description="SideFit 백엔드 API 서버",
    version="0.1.0",
)

app.include_router(api_router)