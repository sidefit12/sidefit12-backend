"""SQLAlchemy 데이터베이스 연결과 세션을 관리하는 모듈."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """모든 SQLAlchemy ORM 모델이 상속하는 기본 클래스."""

    pass


def get_db() -> Generator[Session, None, None]:
    """요청 단위의 데이터베이스 세션을 생성하고 반환한다.

    FastAPI 요청 처리가 끝나면 finally 블록에서 세션을 닫아
    데이터베이스 연결이 반환되도록 한다.

    Yields:
        현재 요청에서 사용할 SQLAlchemy 세션
    """
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
