"""애플리케이션 환경설정을 관리하는 모듈."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """환경변수와 .env 파일에서 애플리케이션 설정을 불러온다."""

    database_url: str

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