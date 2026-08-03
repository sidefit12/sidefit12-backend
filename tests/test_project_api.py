"""PROJECT-001~005 프로젝트 모집 API 통합 테스트."""

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_token
from app.domains.roles.models import Role
from app.domains.tech_stacks.models import TechStack
from app.domains.topics.models import Topic
from app.domains.users.models import User
from tests.conftest import SentEmailStore
from tests.test_auth_api import dispatch_and_confirm, signup


def _headers(client: TestClient, emails: SentEmailStore) -> dict[str, str]:
    data = signup(client, dispatch_and_confirm(client, emails))
    return {"Authorization": f"Bearer {data['accessToken']}"}


def _other_headers(db: Session) -> dict[str, str]:
    user = User(
        email="other@example.com",
        password_hash="unused",
        nickname="otheruser",
        user_status="ACTIVE",
    )
    db.add(user)
    db.commit()
    token = create_token(user.user_id, token_type="access", expires_delta=timedelta(minutes=10))
    return {"Authorization": f"Bearer {token}"}


def _options(db: Session) -> tuple[Topic, TechStack, Role]:
    topic = Topic(topic_code="WEB", topic_name="웹 서비스")
    tech = TechStack(tech_stack_code="FASTAPI", tech_stack_name="FastAPI", category="BACKEND")
    role = Role(role_code="BACKEND", role_name="백엔드 개발자")
    db.add_all([topic, tech, role])
    db.commit()
    return topic, tech, role


def _payload(topic: Topic, tech: TechStack, role: Role) -> dict:
    return {
        "title": "함께 만드는 사이드 프로젝트",
        "summary": "FastAPI 기반 매칭 서비스를 만듭니다.",
        "description": "사용자에게 잘 맞는 프로젝트를 추천하는 서비스를 함께 개발합니다.",
        "workType": "HYBRID",
        "region": "서울",
        "weeklyHours": 10,
        "recruitmentDeadline": (datetime.now(timezone.utc) + timedelta(days=14)).isoformat(),
        "recruitmentStatus": "RECRUITING",
        "topics": [{"topicId": topic.topic_id, "isPrimary": True}],
        "techStacks": [
            {
                "techStackId": tech.tech_stack_id,
                "requirementType": "REQUIRED",
                "requiredLevel": "INTERMEDIATE",
            }
        ],
        "positions": [
            {
                "roleId": role.role_id,
                "positionTitle": "백엔드 개발자",
                "responsibilities": "API와 데이터 모델 설계",
                "requiredCount": 2,
                "requiredLevel": "INTERMEDIATE",
            }
        ],
        "collaborationChannels": [
            {
                "channelType": "DISCORD",
                "channelName": "개발 채널",
                "channelUrl": "https://discord.com/channels/example",
            }
        ],
    }


def test_project_crud_filter_permission_and_soft_delete(
    client: TestClient, db_session: Session, sent_emails: SentEmailStore
) -> None:
    topic, tech, role = _options(db_session)
    headers = _headers(client, sent_emails)
    created = client.post("/api/v1/projects", headers=headers, json=_payload(topic, tech, role))
    assert created.status_code == 201
    project_id = created.json()["data"]["projectId"]
    assert created.json()["data"]["topics"][0]["isPrimary"] is True
    assert created.json()["data"]["positions"][0]["roleCode"] == "BACKEND"

    listed = client.get(
        f"/api/v1/projects?topicId={topic.topic_id}&roleId={role.role_id}", headers=headers
    )
    assert listed.status_code == 200
    assert listed.json()["data"]["total"] == 1

    detail = client.get(f"/api/v1/projects/{project_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["data"]["title"] == "함께 만드는 사이드 프로젝트"

    forbidden = client.patch(
        f"/api/v1/projects/{project_id}",
        headers=_other_headers(db_session),
        json={"title": "권한 없는 수정"},
    )
    assert forbidden.status_code == 403
    assert forbidden.json()["code"] == "PROJECT_PERMISSION_DENIED"

    updated = client.patch(
        f"/api/v1/projects/{project_id}",
        headers=headers,
        json={"title": "수정된 사이드 프로젝트", "recruitmentStatus": "CLOSED"},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["closedAt"] is not None

    deleted = client.request(
        "DELETE",
        f"/api/v1/projects/{project_id}",
        headers=headers,
        json={"reason": "프로젝트 모집 계획 변경"},
    )
    assert deleted.status_code == 200
    assert deleted.json()["data"]["deleted"] is True
    assert client.get(f"/api/v1/projects/{project_id}", headers=headers).status_code == 404


def test_project_rejects_inactive_reference_and_requires_authentication(
    client: TestClient, db_session: Session, sent_emails: SentEmailStore
) -> None:
    topic, tech, role = _options(db_session)
    topic.is_active = False
    db_session.commit()
    response = client.post(
        "/api/v1/projects", headers=_headers(client, sent_emails), json=_payload(topic, tech, role)
    )
    assert response.status_code == 422
    assert response.json()["code"] == "INVALID_PROJECT_SELECTION"
    assert client.get("/api/v1/projects").status_code == 401


def test_project_swagger_documents_korean_operations(client: TestClient) -> None:
    """프로젝트 API의 Swagger 설명과 오류 응답이 한글로 등록되는지 확인한다."""
    paths = client.get("/openapi.json").json()["paths"]
    collection = paths["/api/v1/projects"]
    detail = paths["/api/v1/projects/{project_id}"]

    assert collection["post"]["summary"] == "프로젝트 모집 글 생성"
    assert collection["get"]["summary"] == "프로젝트 모집 글 목록 조회"
    assert detail["get"]["summary"] == "프로젝트 모집 글 상세 조회"
    assert detail["patch"]["summary"] == "프로젝트 모집 글 수정"
    assert detail["delete"]["summary"] == "프로젝트 모집 글 삭제"
    assert collection["post"]["security"] == [{"BearerAuth": []}]
    assert "401" in collection["post"]["responses"]
    assert "403" in detail["patch"]["responses"]
    query_parameters = {item["name"]: item for item in collection["get"]["parameters"]}
    assert query_parameters["recruitmentStatus"]["description"] == "모집 상태"
