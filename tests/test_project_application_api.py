"""Excel API 명세서의 APP-001~007 프로젝트 지원 통합 테스트."""

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_token
from app.domains.notifications.models import Notification
from app.domains.project_member_events.models import ProjectMemberEvent
from app.domains.project_members.models import ProjectMember
from app.domains.project_positions.models import ProjectPosition
from app.domains.projects.models import Project
from app.domains.roles.models import Role
from app.domains.tech_stacks.models import TechStack
from app.domains.user_profiles.models import UserProfile, UserTechStack
from app.domains.users.models import User


def _header(user: User) -> dict[str, str]:
    token = create_token(user.user_id, token_type="access", expires_delta=timedelta(minutes=10))
    return {"Authorization": f"Bearer {token}"}


def _seed(db: Session, *, required_count: int = 1):
    owner = User(
        email="owner@sidefit.dev",
        password_hash="hashed",
        nickname="프로젝트장",
        user_status="ACTIVE",
        system_role="USER",
    )
    applicant = User(
        email="applicant@sidefit.dev",
        password_hash="hashed",
        nickname="지원자",
        user_status="ACTIVE",
        system_role="USER",
    )
    db.add_all([owner, applicant])
    db.flush()
    db.add(UserProfile(user_id=applicant.user_id, introduction="백엔드 개발자입니다."))
    tech_stack = TechStack(
        tech_stack_code="SPRING_BOOT",
        tech_stack_name="Spring Boot",
        category="BACKEND",
    )
    db.add(tech_stack)
    db.flush()
    db.add(
        UserTechStack(
            user_id=applicant.user_id,
            tech_stack_id=tech_stack.tech_stack_id,
            proficiency_level="INTERMEDIATE",
            experience_months=12,
            is_learning=False,
        )
    )
    role = Role(role_code="BACKEND", role_name="백엔드 개발자")
    db.add(role)
    db.flush()
    project = Project(
        owner_user_id=owner.user_id,
        title="지원 API 테스트 프로젝트",
        summary="지원 API의 전체 상태 전이를 검증합니다.",
        description="프로젝트 지원부터 승인까지 검증하는 프로젝트입니다.",
        work_type="ONLINE",
        recruitment_deadline=datetime.now(timezone.utc) + timedelta(days=10),
        recruitment_status="RECRUITING",
        project_status="PREPARING",
        visibility="PUBLIC",
    )
    db.add(project)
    db.flush()
    position = ProjectPosition(
        project_id=project.project_id,
        role_id=role.role_id,
        position_title="백엔드 개발자",
        required_count=required_count,
        position_status="OPEN",
    )
    db.add(position)
    db.commit()
    return owner, applicant, project, position


def _apply(client: TestClient, applicant: User, project: Project, position: ProjectPosition):
    return client.post(
        f"/api/v1/projects/{project.project_id}/applications",
        headers=_header(applicant),
        json={
            "applicationMessage": "백엔드 API 개발 경험으로 프로젝트에 기여하겠습니다.",
            "projectPositionId": position.project_position_id,
        },
    )


def _apply_idempotently(
    client: TestClient, applicant: User, project: Project, position: ProjectPosition
):
    headers = {**_header(applicant), "Idempotency-Key": "application-test-key"}
    return client.post(
        f"/api/v1/projects/{project.project_id}/applications",
        headers=headers,
        json={
            "applicationMessage": "백엔드 API 개발 경험으로 프로젝트에 기여하겠습니다.",
            "projectPositionId": position.project_position_id,
        },
    )


def test_application_create_list_detail_and_accept(client: TestClient, db_session: Session) -> None:
    """지원 생성부터 소유자 승인과 팀원 생성까지 하나의 흐름으로 검증한다."""
    owner, applicant, project, position = _seed(db_session)

    created = _apply_idempotently(client, applicant, project, position)
    assert created.status_code == 201
    application_id = created.json()["data"]["applicationId"]
    assert created.json()["data"]["applicationStatus"] == "PENDING"
    assert db_session.query(Notification).filter_by(notification_type="APPLICATION_RECEIVED").one()

    repeated = _apply_idempotently(client, applicant, project, position)
    assert repeated.status_code == 201
    assert repeated.json()["data"]["applicationId"] == application_id

    duplicate = _apply(client, applicant, project, position)
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "ALREADY_APPLIED"

    mine = client.get("/api/v1/users/me/applications", headers=_header(applicant))
    assert mine.status_code == 200
    assert mine.json()["data"]["statusCounts"] == {"PENDING": 1}
    assert mine.json()["data"]["items"][0]["projectTitle"] == project.title
    assert mine.json()["data"]["items"][0]["positionTitle"] == position.position_title
    assert mine.json()["data"]["items"][0]["applicantTechStacks"] == ["Spring Boot"]
    assert mine.json()["data"]["items"][0]["applicant"]["techStacks"] == ["Spring Boot"]

    applicants = client.get(
        f"/api/v1/projects/{project.project_id}/applications", headers=_header(owner)
    )
    assert applicants.status_code == 200
    assert applicants.json()["data"]["items"][0]["applicant"]["nickname"] == "지원자"

    detail = client.get(f"/api/v1/applications/{application_id}", headers=_header(owner))
    assert detail.status_code == 200
    assert detail.json()["data"]["applicantProfile"]["introduction"] == "백엔드 개발자입니다."
    assert detail.json()["data"]["submittedSnapshot"] is None

    accepted = client.patch(
        f"/api/v1/applications/{application_id}/accept",
        headers=_header(owner),
        json={"note": "합류를 환영합니다."},
    )
    assert accepted.status_code == 200
    assert accepted.json()["data"]["application"]["applicationStatus"] == "ACCEPTED"
    assert accepted.json()["data"]["positionSummary"] == {
        "requiredCount": 1,
        "acceptedCount": 1,
        "positionStatus": "CLOSED",
    }
    assert db_session.query(ProjectMember).filter_by(member_type="MEMBER").one()
    assert db_session.query(ProjectMemberEvent).filter_by(event_type="JOINED").one()
    assert db_session.query(Notification).filter_by(notification_type="APPLICATION_ACCEPTED").one()


def test_application_cancel_reactivate_reject_and_permissions(
    client: TestClient, db_session: Session
) -> None:
    """지원 취소 재요청, 취소 건 재활성화, 거절 및 접근 권한을 검증한다."""
    owner, applicant, project, position = _seed(db_session, required_count=2)
    application_id = _apply(client, applicant, project, position).json()["data"]["applicationId"]
    outsider = User(
        email="outsider@sidefit.dev",
        password_hash="hashed",
        nickname="외부 사용자",
        user_status="ACTIVE",
        system_role="USER",
    )
    db_session.add(outsider)
    db_session.commit()

    forbidden = client.get(
        f"/api/v1/applications/{application_id}",
        headers=_header(outsider),
    )
    assert forbidden.status_code == 403
    assert forbidden.json()["code"] == "ACCESS_DENIED"

    canceled = client.patch(
        f"/api/v1/applications/{application_id}/cancel",
        headers=_header(applicant),
        json={"reason": "개인 일정으로 지원을 취소합니다."},
    )
    assert canceled.status_code == 200
    assert canceled.json()["data"]["applicationStatus"] == "CANCELED"

    reactivated = _apply(client, applicant, project, position)
    assert reactivated.status_code == 201
    assert reactivated.json()["data"]["applicationId"] == application_id

    rejected = client.patch(
        f"/api/v1/applications/{application_id}/reject",
        headers=_header(owner),
        json={
            "rejectionReasonCode": "ROLE_MISMATCH",
            "rejectionReason": "요구 경험과 차이가 있습니다.",
        },
    )
    assert rejected.status_code == 200
    assert rejected.json()["data"]["application"]["applicationStatus"] == "REJECTED"
    assert rejected.json()["data"]["application"]["rejectionReason"].startswith("ROLE_MISMATCH")


def test_application_swagger_contract(client: TestClient) -> None:
    """APP-001~007의 한글 Swagger 설명과 요청·응답 예시를 검증한다."""
    schema = client.get("/openapi.json").json()
    operations = [
        ("/api/v1/projects/{projectId}/applications", "post", "APP_001"),
        ("/api/v1/users/me/applications", "get", "APP_002"),
        ("/api/v1/applications/{applicationId}/cancel", "patch", "APP_003"),
        ("/api/v1/projects/{projectId}/applications", "get", "APP_004"),
        ("/api/v1/applications/{applicationId}", "get", "APP_005"),
        ("/api/v1/applications/{applicationId}/accept", "patch", "APP_006"),
        ("/api/v1/applications/{applicationId}/reject", "patch", "APP_007"),
    ]
    for path, method, operation_id in operations:
        operation = schema["paths"][path][method]
        assert operation["operationId"] == operation_id
        assert operation["summary"]
        assert operation["responses"]["200" if method != "post" else "201"]["content"][
            "application/json"
        ]["example"]
    fields = schema["components"]["schemas"]["ApplicationCreateRequest"]["properties"]
    assert fields["applicationMessage"]["description"] == "지원 메시지"
