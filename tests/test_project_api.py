"""Excel API 명세서의 PROJECT-001~007, PROJECT-009 통합 테스트."""

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domains.project_member_events.models import ProjectMemberEvent
from app.domains.project_members.models import ProjectMember
from app.domains.roles.models import Role
from app.domains.tech_stacks.models import TechStack
from app.domains.topics.models import Topic
from tests.conftest import SentEmailStore
from tests.test_auth_api import dispatch_and_confirm, signup


def _headers(client: TestClient, emails: SentEmailStore) -> dict[str, str]:
    data = signup(client, dispatch_and_confirm(client, emails))
    return {"Authorization": f"Bearer {data['accessToken']}", "Idempotency-Key": "project-test-key"}


def _options(db: Session):
    topic = Topic(topic_code="WEB", topic_name="웹 서비스")
    tech = TechStack(tech_stack_code="FASTAPI", tech_stack_name="FastAPI", category="Backend")
    role = Role(role_code="BACKEND", role_name="백엔드")
    db.add_all([topic, tech, role])
    db.commit()
    return topic, tech, role


def _payload(topic, tech, role):
    return {
        "title": "AI 기반 자산관리 프로젝트",
        "summary": "개인화 자산관리 웹 서비스를 함께 만듭니다.",
        "description": "<script>제거</script> 프로젝트 목표와 진행 방식을 자세히 설명합니다.",
        "expectedStartDate": "2026-09-01",
        "expectedEndDate": "2026-12-31",
        "positions": [
            {
                "positionTitle": "백엔드 개발자",
                "requiredCount": 2,
                "requiredLevel": "BEGINNER",
                "responsibilities": "API와 DB 설계",
                "roleId": role.role_id,
            }
        ],
        "recruitmentDeadline": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        "region": "서울 강남",
        "techStacks": [
            {
                "requiredLevel": "BEGINNER",
                "requirementType": "REQUIRED",
                "techStackId": tech.tech_stack_id,
            }
        ],
        "topicIds": [topic.topic_id],
        "visibility": "PUBLIC",
        "weeklyHours": 10,
        "workType": "HYBRID",
    }


def test_project_api_spec_flow(
    client: TestClient, db_session: Session, sent_emails: SentEmailStore
) -> None:
    topic, tech, role = _options(db_session)
    headers = _headers(client, sent_emails)
    payload = _payload(topic, tech, role)
    created = client.post("/api/v1/projects", headers=headers, json=payload)
    assert created.status_code == 201
    data = created.json()["data"]
    project_id = data["project"]["projectId"]
    assert data["project"]["recruitmentStatus"] == "DRAFT"
    assert "script" not in data["description"]
    assert (
        db_session.query(ProjectMember).filter_by(project_id=project_id, member_type="OWNER").one()
    )
    assert db_session.query(ProjectMemberEvent).filter_by(event_type="JOINED").one()

    repeated = client.post("/api/v1/projects", headers=headers, json=payload)
    assert repeated.status_code == 201
    assert repeated.json()["data"]["project"]["projectId"] == project_id

    recruiting = client.patch(
        f"/api/v1/projects/{project_id}/recruitment-status",
        headers=headers,
        json={"recruitmentStatus": "RECRUITING"},
    )
    assert recruiting.status_code == 200
    assert recruiting.json()["data"]["recruitmentStatus"] == "RECRUITING"

    listed = client.get(
        f"/api/v1/projects?page=0&topicIds={topic.topic_id}&techStackIds={tech.tech_stack_id}&roleIds={role.role_id}"
    )
    assert listed.status_code == 200
    assert listed.json()["data"]["items"][0]["projectId"] == project_id
    assert listed.json()["meta"]["page"] == 0
    assert "requestId" in listed.json()

    detail = client.get(f"/api/v1/projects/{project_id}")
    assert detail.status_code == 200
    assert detail.json()["data"]["project"]["viewCount"] == 1

    updated = client.patch(
        f"/api/v1/projects/{project_id}",
        headers=headers,
        json={"title": "수정된 자산관리 프로젝트"},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["project"]["title"] == "수정된 자산관리 프로젝트"

    started = client.patch(
        f"/api/v1/projects/{project_id}/status",
        headers=headers,
        json={"projectStatus": "IN_PROGRESS"},
    )
    assert started.status_code == 200
    assert started.json()["data"]["projectStatus"] == "IN_PROGRESS"

    mine = client.get("/api/v1/users/me/projects?page=0&size=20", headers=headers)
    assert mine.status_code == 200
    assert mine.json()["data"]["items"][0]["projectId"] == project_id

    deleted = client.request(
        "DELETE",
        f"/api/v1/projects/{project_id}",
        headers=headers,
        json={"deletionReason": "프로젝트 계획 변경으로 모집을 종료합니다."},
    )
    assert deleted.status_code == 204
    assert deleted.content == b""
    assert client.get(f"/api/v1/projects/{project_id}").status_code == 404


def test_project_reference_and_swagger_contract(
    client: TestClient, db_session: Session, sent_emails: SentEmailStore
) -> None:
    topic, tech, role = _options(db_session)
    topic.is_active = False
    db_session.commit()
    response = client.post(
        "/api/v1/projects", headers=_headers(client, sent_emails), json=_payload(topic, tech, role)
    )
    assert response.status_code == 404
    assert response.json()["code"] == "TOPIC_NOT_FOUND"

    openapi = client.get("/openapi.json").json()
    paths = openapi["paths"]
    assert paths["/api/v1/projects"]["get"]["operationId"] == "PROJECT_001_list"
    assert paths["/api/v1/projects"]["post"]["operationId"] == "PROJECT_002_create"
    assert (
        paths["/api/v1/projects/{project_id}/recruitment-status"]["patch"]["operationId"]
        == "PROJECT_006_recruitment_status"
    )
    assert paths["/api/v1/users/me/projects"]["get"]["operationId"] == "PROJECT_009_my_projects"
    create_fields = openapi["components"]["schemas"]["ProjectCreateRequest"]["properties"]
    assert create_fields["title"]["description"] == "프로젝트 제목"
    assert create_fields["description"]["description"] == "프로젝트 상세 설명"
    delete_fields = openapi["components"]["schemas"]["ProjectDeleteRequest"]["properties"]
    assert delete_fields["deletionReason"]["description"] == "프로젝트 삭제 사유"
    create_content = paths["/api/v1/projects"]["post"]["requestBody"]["content"]["application/json"]
    assert create_content["examples"]["default"]["value"]["title"] == "AI 기반 자산관리 프로젝트"
    assert (
        paths["/api/v1/projects"]["post"]["responses"]["201"]["content"]["application/json"][
            "example"
        ]["data"]["project"]["projectId"]
        == 100
    )
    delete_content = paths["/api/v1/projects/{project_id}"]["delete"]["requestBody"]["content"][
        "application/json"
    ]
    assert "deletionReason" in delete_content["examples"]["default"]["value"]
    assert "content" not in paths["/api/v1/projects/{project_id}"]["delete"]["responses"]["204"]
