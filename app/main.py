from fastapi import FastAPI

app = FastAPI(
    title="SideFit API",
    description="SideFit 백엔드 API 서버",
    version="0.1.0",
)

@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "message": "SideFit API 서버가 정상적으로 실행되었습니다."
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok"
    }