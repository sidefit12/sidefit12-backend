"""애플리케이션 환경설정을 관리하는 모듈."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """환경변수와 .env 파일에서 애플리케이션 설정을 불러온다."""

    database_url: str
    jwt_secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 14
    maileroo_api_key: str
    maileroo_from_email: str
    maileroo_from_name: str = "SideFit"
    maileroo_api_url: str = "https://smtp.maileroo.com/api/v2/emails"
    frontend_password_reset_url: str = "http://localhost:3000/password-reset"
    cors_origins: str = "http://localhost:5173"
    log_level: str = "INFO"
    storage_endpoint_url: str | None = None
    storage_access_key: str | None = None
    storage_secret_key: str | None = None
    storage_bucket: str | None = None
    storage_region: str = "ap-northeast-2"
    storage_public_base_url: str | None = None
    gemini_api_key: str | None = None
    gemini_embedding_model: str = "gemini-embedding-001"
    gemini_embedding_dimension: int = 768
    gemini_embedding_version: str = "gemini-embedding-001-768-v1"
    firebase_credentials_path: str | None = None
    firebase_credentials_base64: str | None = None
    firebase_project_id: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """캐시된 애플리케이션 설정 객체를 반환한다.

    동일한 설정 객체를 반복해서 생성하거나 .env 파일을 매번 읽지 않도록
    최초 생성된 Settings 객체를 캐시에 저장한다.

    Returns:
        환경변수가 적용된 애플리케이션 설정 객체
    """
    return Settings()
