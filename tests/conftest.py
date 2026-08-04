"""API 테스트에서 공통으로 사용하는 격리 DB와 client fixture."""

from collections.abc import Generator
from dataclasses import dataclass, field

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import BigInteger, create_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.core.database import Base, get_db
from app.domains.email_verifications import models as email_verification_models  # noqa: F401
from app.domains.files import models as file_models  # noqa: F401
from app.domains.idempotency_requests import models as idempotency_models  # noqa: F401
from app.domains.notification_preferences import (
    models as notification_preference_models,  # noqa: F401
)
from app.domains.notifications import models as notification_models  # noqa: F401
from app.domains.project_applications import models as application_models  # noqa: F401
from app.domains.project_bookmarks import models as bookmark_models  # noqa: F401
from app.domains.project_collaboration_channels import models as channel_models  # noqa: F401
from app.domains.project_member_events import models as member_event_models  # noqa: F401
from app.domains.project_members import models as member_models  # noqa: F401
from app.domains.project_positions import models as position_models  # noqa: F401
from app.domains.project_reviews import models as review_models  # noqa: F401
from app.domains.projects import models as project_models  # noqa: F401
from app.domains.recommendation_reasons import models as recommendation_reason_models  # noqa: F401
from app.domains.recommendation_results import models as recommendation_result_models  # noqa: F401
from app.domains.refresh_tokens import models as refresh_token_models  # noqa: F401
from app.domains.reports import models as report_models  # noqa: F401
from app.domains.roles import models as role_models  # noqa: F401
from app.domains.tech_stacks import models as tech_stack_models  # noqa: F401
from app.domains.topics import models as topic_models  # noqa: F401
from app.domains.user_profiles import models as profile_models  # noqa: F401
from app.domains.users import models as user_models  # noqa: F401
from app.integrations.maileroo import MailerooEmailService
from app.main import app


@compiles(BigInteger, "sqlite")
def compile_big_integer_for_sqlite(_type: BigInteger, _compiler, **_kwargs) -> str:
    """SQLite 테스트에서 BIGINT PK가 자동 증가하도록 INTEGER로 변환한다."""
    return "INTEGER"


@dataclass
class SentEmailStore:
    """외부 이메일 발송 대신 테스트 인증번호를 보관한다."""

    messages: list[dict[str, str]] = field(default_factory=list)
    password_resets: list[dict[str, str]] = field(default_factory=list)

    @property
    def latest_code(self) -> str:
        """마지막으로 발송된 인증번호를 반환한다."""
        return self.messages[-1]["code"]

    @property
    def latest_reset_token(self) -> str:
        """마지막으로 발송된 비밀번호 재설정 토큰을 반환한다."""
        return self.password_resets[-1]["reset_token"]


@pytest.fixture(autouse=True)
def test_jwt_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    """JWT 테스트가 운영 비밀키와 무관하게 충분히 긴 전용 키를 사용하게 한다."""
    monkeypatch.setattr(
        get_settings(),
        "jwt_secret_key",
        "sidefit-test-jwt-secret-key-32-bytes-minimum",
    )


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """테스트마다 새 메모리 DB와 SQLAlchemy session을 제공한다."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)
    Base.metadata.create_all(engine)
    session = testing_session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def sent_emails(monkeypatch: pytest.MonkeyPatch) -> SentEmailStore:
    """Maileroo 네트워크 호출을 차단하고 발송 정보를 수집한다."""
    store = SentEmailStore()

    def fake_send(_service: MailerooEmailService, *, to_email: str, code: str) -> str:
        store.messages.append({"to_email": to_email, "code": code})
        return "test-reference-id"

    def fake_send_password_reset(
        _service: MailerooEmailService, *, to_email: str, reset_token: str
    ) -> str:
        store.password_resets.append({"to_email": to_email, "reset_token": reset_token})
        return "test-password-reset-reference-id"

    monkeypatch.setattr(MailerooEmailService, "send_verification_code", fake_send)
    monkeypatch.setattr(MailerooEmailService, "send_password_reset", fake_send_password_reset)
    return store


@pytest.fixture
def client(db_session: Session, sent_emails: SentEmailStore) -> Generator[TestClient, None, None]:
    """테스트 DB dependency가 적용된 FastAPI client를 제공한다."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
