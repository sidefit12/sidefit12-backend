"""기준정보 목록 API의 조회, 권한, Swagger 명세를 검증한다."""

from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_token
from app.domains.roles.models import Role
from app.domains.tech_stacks.models import TechStack
from app.domains.topics.models import Topic
from app.domains.users.models import User


def _seed_reference_data(db: Session) -> None:
    """활성 및 비활성 기준정보 테스트 데이터를 저장한다."""
    db.add_all(
        [
            Topic(topic_code="FINTECH", topic_name="핀테크", is_active=True),
            Topic(topic_code="OLD_TOPIC", topic_name="이전 토픽", is_active=False),
            TechStack(
                tech_stack_code="JAVA",
                tech_stack_name="Java",
                category="언어",
                is_active=True,
            ),
            TechStack(
                tech_stack_code="OLD_JAVA",
                tech_stack_name="Old Java",
                category="언어",
                is_active=False,
            ),
            Role(role_code="BACKEND", role_name="백엔드 개발자", is_active=True),
            Role(role_code="OLD_ROLE", role_name="이전 역할", is_active=False),
        ]
    )
    db.commit()


def test_reference_data_public_lists_only_active_items(
    client: TestClient, db_session: Session
) -> None:
    """비회원 기본 조회는 활성 기준정보만 반환한다."""
    _seed_reference_data(db_session)

    topics = client.get("/api/v1/topics")
    tech_stacks = client.get("/api/v1/tech-stacks", params={"keyword": "java"})
    roles = client.get("/api/v1/roles")

    assert topics.status_code == 200
    assert topics.json()["data"]["items"] == [
        {"topicId": 1, "topicCode": "FINTECH", "topicName": "핀테크", "isActive": True}
    ]
    assert tech_stacks.status_code == 200
    assert [item["techStackCode"] for item in tech_stacks.json()["data"]["items"]] == ["JAVA"]
    assert roles.status_code == 200
    assert [item["roleCode"] for item in roles.json()["data"]["items"]] == ["BACKEND"]
    assert topics.json()["requestId"] != "-"


def test_include_inactive_requires_admin(client: TestClient, db_session: Session) -> None:
    """비활성 기준정보 포함 조회는 관리자에게만 허용한다."""
    _seed_reference_data(db_session)

    forbidden = client.get("/api/v1/topics", params={"includeInactive": "true"})
    assert forbidden.status_code == 403
    assert forbidden.json()["code"] == "ADMIN_PERMISSION_REQUIRED"

    admin = User(
        email="admin@sidefit.dev",
        password_hash="hashed",
        nickname="관리자",
        user_status="ACTIVE",
        system_role="ADMIN",
    )
    db_session.add(admin)
    db_session.commit()
    token = create_token(admin.user_id, token_type="access", expires_delta=timedelta(minutes=5))

    response = client.get(
        "/api/v1/topics",
        params={"includeInactive": "true"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert {item["topicCode"] for item in response.json()["data"]["items"]} == {
        "FINTECH",
        "OLD_TOPIC",
    }


def test_reference_data_openapi_has_korean_descriptions_and_examples(
    client: TestClient,
) -> None:
    """세 기준정보 API의 Swagger 설명과 응답 예시를 검증한다."""
    schema = client.get("/openapi.json").json()
    expected = {
        "/api/v1/topics": ("MASTER_001_list_topics", "토픽 목록 조회"),
        "/api/v1/tech-stacks": ("MASTER_002_list_tech_stacks", "기술 스택 목록 조회"),
        "/api/v1/roles": ("MASTER_003_list_roles", "역할 목록 조회"),
    }

    for path, (operation_id, summary) in expected.items():
        operation = schema["paths"][path]["get"]
        assert operation["operationId"] == operation_id
        assert operation["summary"] == summary
        assert operation["parameters"][0]["description"]
        assert operation["responses"]["200"]["content"]["application/json"]["example"]
