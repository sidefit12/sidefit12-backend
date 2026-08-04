"""INT-001~003 추천 갱신·모집 자동 종료·도메인 알림 내부 처리 테스트."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.domains.internal_processing.schemas import (
    DomainNotificationEvent,
    RecommendationUpdateEvent,
)
from app.domains.internal_processing.service import InternalProcessingService
from app.domains.notifications.models import Notification
from app.domains.project_members.models import ProjectMember
from app.domains.project_positions.models import ProjectPosition
from app.domains.projects.models import Project
from app.domains.recommendation_results.models import RecommendationResult
from app.domains.roles.models import Role
from app.domains.user_profiles.models import UserProfile
from app.domains.users.models import User


def _user(db: Session, suffix: str) -> User:
    user = User(
        email=f"internal-{suffix}@sidefit.dev",
        password_hash="hash",
        nickname=f"내부처리{suffix}",
        user_status="ACTIVE",
        system_role="USER",
    )
    db.add(user)
    db.flush()
    db.add(UserProfile(user_id=user.user_id, onboarding_completed=True))
    return user


def _project(
    db: Session, owner: User, role: Role, suffix: str, *, deadline: datetime, required: int = 1
):
    project = Project(
        owner_user_id=owner.user_id,
        title=f"내부 처리 프로젝트 {suffix}",
        summary="내부 처리 기능 검증을 위한 프로젝트입니다.",
        description="<b>추천 정규화</b>와 모집 자동 종료를 검증합니다.",
        work_type="ONLINE",
        recruitment_deadline=deadline,
        recruitment_status="RECRUITING",
        project_status="PREPARING",
        visibility="PUBLIC",
        moderation_status="VISIBLE",
    )
    db.add(project)
    db.flush()
    position = ProjectPosition(
        project_id=project.project_id,
        role_id=role.role_id,
        position_title="개발자",
        required_count=required,
        position_status="OPEN",
    )
    db.add(position)
    db.flush()
    return project, position


def test_int_001_recommendation_data_refresh_is_idempotent(db_session: Session):
    """사용자·프로젝트 변경 시 추천 결과 무효화와 정규화 버전을 검증한다."""
    owner = _user(db_session, "owner")
    viewer = _user(db_session, "viewer")
    role = Role(role_code="INT_RECO", role_name="내부 추천 역할")
    db_session.add(role)
    db_session.flush()
    project, _ = _project(
        db_session,
        owner,
        role,
        "recommendation",
        deadline=datetime.now(timezone.utc) + timedelta(days=3),
    )
    db_session.add(
        RecommendationResult(
            user_id=viewer.user_id,
            project_id=project.project_id,
            rule_score=Decimal("0.5000"),
            final_score=Decimal("0.5000"),
            recommendation_version="rule-v1",
        )
    )
    db_session.commit()

    result = InternalProcessingService.refresh_recommendation_data(
        db_session,
        RecommendationUpdateEvent(target_type="PROJECT", target_id=project.project_id),
    )
    db_session.refresh(project)
    assert result.processed_count == 1
    assert project.embedding_version == "normalized-v1"
    assert "<b>" not in project.normalized_text
    assert db_session.query(RecommendationResult).count() == 0

    repeated = InternalProcessingService.refresh_recommendation_data(
        db_session,
        RecommendationUpdateEvent(target_type="PROJECT", target_id=project.project_id),
    )
    assert repeated.processed_count == 0


def test_int_002_closes_expired_and_filled_projects(db_session: Session):
    """기한 경과 및 모든 포지션 충원 조건과 반복 실행 멱등성을 검증한다."""
    owner = _user(db_session, "close-owner")
    member = _user(db_session, "close-member")
    role = Role(role_code="INT_CLOSE", role_name="내부 마감 역할")
    db_session.add(role)
    db_session.flush()
    now = datetime.now(timezone.utc)
    expired, _ = _project(db_session, owner, role, "expired", deadline=now - timedelta(minutes=1))
    filled, filled_position = _project(
        db_session, owner, role, "filled", deadline=now + timedelta(days=2)
    )
    open_project, _ = _project(
        db_session, owner, role, "open", deadline=now + timedelta(days=2), required=2
    )
    db_session.add(
        ProjectMember(
            project_id=filled.project_id,
            user_id=member.user_id,
            project_position_id=filled_position.project_position_id,
            member_type="MEMBER",
            member_status="ACTIVE",
        )
    )
    db_session.commit()

    result = InternalProcessingService.close_recruitment(db_session, now=now)
    assert result.processed_count == 2
    db_session.refresh(expired)
    db_session.refresh(filled)
    db_session.refresh(open_project)
    assert expired.recruitment_status == "CLOSED"
    assert filled.recruitment_status == "CLOSED"
    assert open_project.recruitment_status == "RECRUITING"
    assert (
        db_session.query(Notification).filter_by(notification_type="RECRUITMENT_CLOSED").count()
        == 2
    )
    assert InternalProcessingService.close_recruitment(db_session, now=now).processed_count == 0


def test_int_003_domain_notification_prevents_duplicates(db_session: Session):
    """동일 도메인 이벤트의 알림이 한 번만 저장되는지 검증한다."""
    user = _user(db_session, "notification")
    db_session.commit()
    event = DomainNotificationEvent(
        event_type="APPLICATION_ACCEPTED",
        recipient_user_id=user.user_id,
        application_id=900,
    )
    first = InternalProcessingService.create_domain_notification(db_session, event)
    second = InternalProcessingService.create_domain_notification(db_session, event)
    assert first.processed_count == 1
    assert second.processed_count == 0
    assert db_session.query(Notification).count() == 1
