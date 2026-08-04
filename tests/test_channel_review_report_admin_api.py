"""CHANNEL-001~004, REVIEW-001~004, REPORT-001~002, ADMIN-001~003 통합 테스트."""

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_token
from app.domains.project_members.models import ProjectMember
from app.domains.project_positions.models import ProjectPosition
from app.domains.projects.models import Project
from app.domains.roles.models import Role
from app.domains.user_profiles.models import UserProfile
from app.domains.users.models import User


def _headers(user: User):
    token = create_token(user.user_id, token_type="access", expires_delta=timedelta(minutes=10))
    return {"Authorization": f"Bearer {token}"}


def _seed(db: Session):
    owner = User(
        email="remain-owner@sidefit.dev",
        password_hash="hash",
        nickname="남은기능팀장",
        user_status="ACTIVE",
        system_role="USER",
    )
    member = User(
        email="remain-member@sidefit.dev",
        password_hash="hash",
        nickname="남은기능팀원",
        user_status="ACTIVE",
        system_role="USER",
    )
    outsider = User(
        email="remain-outsider@sidefit.dev",
        password_hash="hash",
        nickname="남은기능외부인",
        user_status="ACTIVE",
        system_role="USER",
    )
    admin = User(
        email="remain-admin@sidefit.dev",
        password_hash="hash",
        nickname="남은기능관리자",
        user_status="ACTIVE",
        system_role="ADMIN",
    )
    db.add_all([owner, member, outsider, admin])
    db.flush()
    db.add_all(
        [
            UserProfile(user_id=x.user_id, onboarding_completed=True)
            for x in (owner, member, outsider, admin)
        ]
    )
    role = Role(role_code="REMAIN_ROLE", role_name="남은 기능 역할")
    db.add(role)
    db.flush()
    project = Project(
        owner_user_id=owner.user_id,
        title="남은 기능 프로젝트",
        summary="협업 채널과 리뷰 및 신고 기능을 검증합니다.",
        description="완료된 프로젝트의 남은 기능을 통합 검증합니다.",
        work_type="ONLINE",
        recruitment_deadline=datetime.now(timezone.utc) + timedelta(days=3),
        recruitment_status="CLOSED",
        project_status="COMPLETED",
        visibility="PUBLIC",
        moderation_status="VISIBLE",
    )
    db.add(project)
    db.flush()
    position = ProjectPosition(
        project_id=project.project_id,
        role_id=role.role_id,
        position_title="개발자",
        required_count=2,
        position_status="CLOSED",
    )
    db.add(position)
    db.flush()
    db.add_all(
        [
            ProjectMember(
                project_id=project.project_id,
                user_id=owner.user_id,
                project_position_id=position.project_position_id,
                member_type="OWNER",
                member_status="ACTIVE",
            ),
            ProjectMember(
                project_id=project.project_id,
                user_id=member.user_id,
                project_position_id=position.project_position_id,
                member_type="MEMBER",
                member_status="ACTIVE",
            ),
        ]
    )
    db.commit()
    return owner, member, outsider, admin, project


def test_channel_crud_and_member_permission(client: TestClient, db_session: Session):
    owner, member, outsider, _, project = _seed(db_session)
    created = client.post(
        f"/api/v1/projects/{project.project_id}/channels",
        headers=_headers(owner),
        json={
            "channelName": "팀 디스코드",
            "channelType": "DISCORD",
            "channelUrl": "https://discord.gg/sidefit",
        },
    )
    assert created.status_code == 201
    channel_id = created.json()["data"]["channelId"]
    assert (
        client.get(
            f"/api/v1/projects/{project.project_id}/channels", headers=_headers(member)
        ).status_code
        == 200
    )
    assert (
        client.get(
            f"/api/v1/projects/{project.project_id}/channels", headers=_headers(outsider)
        ).status_code
        == 403
    )
    changed = client.patch(
        f"/api/v1/projects/{project.project_id}/channels/{channel_id}",
        headers=_headers(owner),
        json={
            "channelName": "팀 슬랙",
            "channelType": "SLACK",
            "channelUrl": "https://sidefit.slack.com",
        },
    )
    assert changed.status_code == 200
    assert changed.json()["data"]["channelType"] == "SLACK"
    assert (
        client.delete(
            f"/api/v1/projects/{project.project_id}/channels/{channel_id}", headers=_headers(owner)
        ).status_code
        == 204
    )
    assert (
        client.get(
            f"/api/v1/projects/{project.project_id}/channels", headers=_headers(member)
        ).json()["data"]["items"]
        == []
    )


def test_review_crud_and_participant_rule(client: TestClient, db_session: Session):
    _, member, outsider, _, project = _seed(db_session)
    assert (
        client.post(
            f"/api/v1/projects/{project.project_id}/reviews",
            headers=_headers(outsider),
            json={"rating": 5},
        ).status_code
        == 403
    )
    created = client.post(
        f"/api/v1/projects/{project.project_id}/reviews",
        headers=_headers(member),
        json={"rating": 5, "content": "좋은 협업 경험이었습니다."},
    )
    assert created.status_code == 201
    review_id = created.json()["data"]["reviewId"]
    assert (
        client.post(
            f"/api/v1/projects/{project.project_id}/reviews",
            headers=_headers(member),
            json={"rating": 4},
        ).status_code
        == 409
    )
    page = client.get(f"/api/v1/projects/{project.project_id}/reviews")
    assert page.status_code == 200 and page.json()["data"]["averageRating"] == 5.0
    assert (
        client.patch(
            f"/api/v1/reviews/{review_id}", headers=_headers(member), json={"rating": 4}
        ).json()["data"]["rating"]
        == 4
    )
    assert (
        client.delete(f"/api/v1/reviews/{review_id}", headers=_headers(member)).status_code == 204
    )


def test_report_and_admin_processing(client: TestClient, db_session: Session):
    owner, _, outsider, admin, project = _seed(db_session)
    assert (
        client.post(
            f"/api/v1/projects/{project.project_id}/reports",
            headers=_headers(owner),
            json={"reasonType": "OTHER"},
        ).status_code
        == 409
    )
    report = client.post(
        f"/api/v1/projects/{project.project_id}/reports",
        headers=_headers(outsider),
        json={"reasonType": "MISLEADING_INFORMATION", "detail": "설명과 실제 안내가 다릅니다."},
    )
    assert report.status_code == 201
    report_id = report.json()["data"]["reportId"]
    assert (
        client.post(
            f"/api/v1/projects/{project.project_id}/reports",
            headers=_headers(outsider),
            json={"reasonType": "OTHER"},
        ).status_code
        == 409
    )
    assert client.get("/api/v1/admin/reports", headers=_headers(outsider)).status_code == 403
    assert (
        client.get("/api/v1/admin/reports", headers=_headers(admin)).json()["meta"]["totalElements"]
        == 1
    )
    processed = client.patch(
        f"/api/v1/admin/reports/{report_id}",
        headers=_headers(admin),
        json={
            "reportStatus": "RESOLVED",
            "resolutionNote": "운영 정책 위반으로 프로젝트를 숨김 처리합니다.",
            "action": "HIDE_PROJECT",
        },
    )
    assert processed.status_code == 200
    db_session.refresh(project)
    assert project.moderation_status == "HIDDEN"


def test_remaining_api_swagger_contract(client: TestClient):
    schema = client.get("/openapi.json").json()
    expected = {
        "CHANNEL_001",
        "CHANNEL_002",
        "CHANNEL_003",
        "CHANNEL_004",
        "REVIEW_001",
        "REVIEW_002",
        "REVIEW_003",
        "REVIEW_004",
        "REPORT_001",
        "REPORT_002",
        "ADMIN_001",
        "ADMIN_002",
        "ADMIN_003",
    }
    actual = {
        operation["operationId"]
        for methods in schema["paths"].values()
        for operation in methods.values()
        if isinstance(operation, dict) and "operationId" in operation
    }
    assert expected <= actual
