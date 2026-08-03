"""Excel API 명세서의 MEMBER-001~005 프로젝트 팀원 통합 테스트."""

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_token
from app.domains.notifications.models import Notification
from app.domains.project_collaboration_channels.models import ProjectCollaborationChannel
from app.domains.project_member_events.models import ProjectMemberEvent
from app.domains.project_members.models import ProjectMember
from app.domains.project_positions.models import ProjectPosition
from app.domains.projects.models import Project
from app.domains.roles.models import Role
from app.domains.user_profiles.models import UserProfile
from app.domains.users.models import User


def _header(user: User) -> dict[str, str]:
    token = create_token(user.user_id, token_type="access", expires_delta=timedelta(minutes=10))
    return {"Authorization": f"Bearer {token}"}


def _seed(db: Session):
    owner = User(
        email="member-owner@sidefit.dev",
        password_hash="hashed",
        nickname="팀장",
        user_status="ACTIVE",
        system_role="USER",
    )
    member_user = User(
        email="member@sidefit.dev",
        password_hash="hashed",
        nickname="팀원",
        user_status="ACTIVE",
        system_role="USER",
    )
    outsider = User(
        email="member-outsider@sidefit.dev",
        password_hash="hashed",
        nickname="외부인",
        user_status="ACTIVE",
        system_role="USER",
    )
    db.add_all([owner, member_user, outsider])
    db.flush()
    db.add_all(
        [
            UserProfile(user_id=owner.user_id, onboarding_completed=True),
            UserProfile(user_id=member_user.user_id, onboarding_completed=True),
        ]
    )
    role = Role(role_code="MEMBER_BACKEND", role_name="팀원 백엔드")
    db.add(role)
    db.flush()
    project = Project(
        owner_user_id=owner.user_id,
        title="팀원 API 테스트 프로젝트",
        summary="팀원 상태 전이와 변경 이력을 검증합니다.",
        description="팀원 목록과 탈퇴, 퇴출, 복구 API를 검증합니다.",
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
        required_count=1,
        position_status="CLOSED",
    )
    db.add(position)
    db.flush()
    owner_member = ProjectMember(
        project_id=project.project_id,
        user_id=owner.user_id,
        project_position_id=position.project_position_id,
        member_type="OWNER",
        member_status="ACTIVE",
    )
    member = ProjectMember(
        project_id=project.project_id,
        user_id=member_user.user_id,
        project_position_id=position.project_position_id,
        member_type="MEMBER",
        member_status="ACTIVE",
    )
    db.add_all([owner_member, member])
    db.flush()
    db.add_all(
        [
            ProjectMemberEvent(
                project_member_id=owner_member.project_member_id,
                event_type="JOINED",
                actor_user_id=owner.user_id,
            ),
            ProjectMemberEvent(
                project_member_id=member.project_member_id,
                event_type="JOINED",
                actor_user_id=owner.user_id,
            ),
            ProjectCollaborationChannel(
                project_id=project.project_id,
                channel_type="DISCORD",
                channel_name="팀 디스코드",
                channel_url="https://discord.gg/sidefit",
                registered_by_user_id=owner.user_id,
            ),
        ]
    )
    db.commit()
    return owner, member_user, outsider, project, position, owner_member, member


def test_member_list_channel_permission_and_event_history(
    client: TestClient, db_session: Session
) -> None:
    """팀원 목록 공개 범위, 협업 채널 권한 및 변경 이력 권한을 검증한다."""
    owner, member_user, outsider, project, position, _, _ = _seed(db_session)

    public_list = client.get(
        f"/api/v1/projects/{project.project_id}/members", headers=_header(outsider)
    )
    assert public_list.status_code == 200
    assert len(public_list.json()["data"]["items"]) == 2
    assert public_list.json()["data"]["channels"] is None
    assert (
        public_list.json()["data"]["positionSummary"][str(position.project_position_id)][
            "activeCount"
        ]
        == 1
    )
    assert all(item["user"]["email"] is None for item in public_list.json()["data"]["items"])

    forbidden_channels = client.get(
        f"/api/v1/projects/{project.project_id}/members?includeChannels=true",
        headers=_header(outsider),
    )
    assert forbidden_channels.status_code == 403

    member_list = client.get(
        f"/api/v1/projects/{project.project_id}/members?includeChannels=true",
        headers=_header(member_user),
    )
    assert member_list.status_code == 200
    assert member_list.json()["data"]["channels"][0]["channelType"] == "DISCORD"
    own = next(
        item
        for item in member_list.json()["data"]["items"]
        if item["user"]["userId"] == member_user.user_id
    )
    assert own["user"]["email"] == member_user.email

    forbidden_events = client.get(
        f"/api/v1/projects/{project.project_id}/member-events", headers=_header(outsider)
    )
    assert forbidden_events.status_code == 403
    events = client.get(
        f"/api/v1/projects/{project.project_id}/member-events", headers=_header(owner)
    )
    assert events.status_code == 200
    assert events.json()["meta"]["totalElements"] == 2


def test_member_remove_restore_and_leave(client: TestClient, db_session: Session) -> None:
    """소유자 퇴출·복구와 팀원 자진 탈퇴 상태 전이를 검증한다."""
    owner, member_user, _, project, position, owner_member, member = _seed(db_session)

    invalid_reason = client.patch(
        f"/api/v1/projects/{project.project_id}/members/{member.project_member_id}/remove",
        headers=_header(owner),
        json={"reason": "짧은 사유"},
    )
    assert invalid_reason.status_code == 400

    removed = client.patch(
        f"/api/v1/projects/{project.project_id}/members/{member.project_member_id}/remove",
        headers=_header(owner),
        json={"reason": "지속적인 무단 불참으로 팀에서 제외합니다."},
    )
    assert removed.status_code == 200
    assert removed.json()["data"]["member"]["memberStatus"] == "REMOVED"
    db_session.refresh(position)
    assert position.position_status == "OPEN"

    restored = client.patch(
        f"/api/v1/projects/{project.project_id}/members/{member.project_member_id}/restore",
        headers=_header(owner),
        json={"reason": "일정 협의 후 프로젝트 팀원으로 복구합니다."},
    )
    assert restored.status_code == 200
    assert restored.json()["data"]["member"]["memberStatus"] == "ACTIVE"
    db_session.refresh(position)
    assert position.position_status == "CLOSED"

    owner_leave = client.patch(
        f"/api/v1/projects/{project.project_id}/members/me/leave",
        headers=_header(owner),
        json={"reason": "프로젝트에서 나갑니다."},
    )
    assert owner_leave.status_code == 400
    assert owner_member.member_status == "ACTIVE"

    left = client.patch(
        f"/api/v1/projects/{project.project_id}/members/me/leave",
        headers=_header(member_user),
        json={"reason": "개인 일정으로 참여가 어렵습니다."},
    )
    assert left.status_code == 200
    assert left.json()["data"]["member"]["memberStatus"] == "LEFT"
    assert left.json()["data"]["member"]["leftAt"] is not None
    event_types = {event.event_type for event in db_session.query(ProjectMemberEvent).all()}
    assert {"LEFT", "REMOVED", "RESTORED"} <= event_types
    notification_types = {item.notification_type for item in db_session.query(Notification).all()}
    assert {"MEMBER_LEFT", "MEMBER_JOINED"} <= notification_types


def test_member_restore_capacity_and_swagger(client: TestClient, db_session: Session) -> None:
    """복구 정원 초과와 MEMBER-001~005 Swagger 계약을 검증한다."""
    owner, _, outsider, project, position, _, member = _seed(db_session)
    member.member_status = "REMOVED"
    member.left_at = datetime.now(timezone.utc)
    replacement = ProjectMember(
        project_id=project.project_id,
        user_id=outsider.user_id,
        project_position_id=position.project_position_id,
        member_type="MEMBER",
        member_status="ACTIVE",
    )
    db_session.add(replacement)
    db_session.commit()

    exceeded = client.patch(
        f"/api/v1/projects/{project.project_id}/members/{member.project_member_id}/restore",
        headers=_header(owner),
        json={"reason": "정원 확인 후 복구를 요청합니다."},
    )
    assert exceeded.status_code == 409
    assert exceeded.json()["code"] == "POSITION_CAPACITY_EXCEEDED"

    schema = client.get("/openapi.json").json()
    operations = [
        ("/api/v1/projects/{projectId}/members", "get", "MEMBER_001"),
        ("/api/v1/projects/{projectId}/members/me/leave", "patch", "MEMBER_002"),
        ("/api/v1/projects/{projectId}/members/{memberId}/remove", "patch", "MEMBER_003"),
        ("/api/v1/projects/{projectId}/members/{memberId}/restore", "patch", "MEMBER_004"),
        ("/api/v1/projects/{projectId}/member-events", "get", "MEMBER_005"),
    ]
    for path, method, operation_id in operations:
        operation = schema["paths"][path][method]
        assert operation["operationId"] == operation_id
        assert operation["summary"]
        assert operation["responses"]["200"]["content"]["application/json"]["example"]
    remove_fields = schema["components"]["schemas"]["MemberRemoveRequest"]["properties"]
    assert "10자" in remove_fields["reason"]["description"]
