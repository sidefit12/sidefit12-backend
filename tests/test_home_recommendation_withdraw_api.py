"""AUTH-012, HOME-001, RECO-001~003 통합 테스트."""

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_token, hash_password
from app.domains.project_positions.models import ProjectPosition
from app.domains.projects.models import Project, ProjectTechStack, ProjectTopic
from app.domains.recommendation_results.models import RecommendationResult
from app.domains.refresh_tokens.models import RefreshToken
from app.domains.roles.models import Role
from app.domains.tech_stacks.models import TechStack
from app.domains.topics.models import Topic
from app.domains.user_profiles.models import UserProfile, UserRole, UserTechStack, UserTopic
from app.domains.users.models import User

PASSWORD = "StrongPassword1!"


def _user(db: Session, suffix: str) -> User:
    user = User(
        email=f"five-api-{suffix}@sidefit.dev",
        password_hash=hash_password(PASSWORD),
        nickname=f"사용자{suffix}",
        user_status="ACTIVE",
        system_role="USER",
    )
    db.add(user)
    db.commit()
    return user


def _headers(user: User) -> dict[str, str]:
    token = create_token(user.user_id, token_type="access", expires_delta=timedelta(minutes=10))
    return {"Authorization": f"Bearer {token}"}


def _references(db: Session):
    topic = Topic(topic_code="RECO_AI", topic_name="인공지능")
    tech = TechStack(tech_stack_code="RECO_FASTAPI", tech_stack_name="FastAPI", category="백엔드")
    role = Role(role_code="RECO_BACKEND", role_name="백엔드")
    db.add_all([topic, tech, role])
    db.commit()
    return topic, tech, role


def _project(
    db: Session, owner: User, topic: Topic, tech: TechStack, role: Role, suffix: str, days: int
):
    project = Project(
        owner_user_id=owner.user_id,
        title=f"추천 프로젝트 {suffix}",
        summary=f"추천 기능 검증을 위한 프로젝트 {suffix}입니다.",
        description="추천 기능과 홈 화면 API 통합 테스트를 위한 충분한 설명입니다.",
        work_type="ONLINE",
        recruitment_deadline=datetime.now(timezone.utc) + timedelta(days=days),
        recruitment_status="RECRUITING",
        project_status="PREPARING",
        visibility="PUBLIC",
        moderation_status="VISIBLE",
    )
    db.add(project)
    db.flush()
    db.add_all(
        [
            ProjectTopic(project_id=project.project_id, topic_id=topic.topic_id, is_primary=True),
            ProjectTechStack(
                project_id=project.project_id,
                tech_stack_id=tech.tech_stack_id,
                requirement_type="REQUIRED",
            ),
            ProjectPosition(
                project_id=project.project_id,
                role_id=role.role_id,
                position_title="백엔드 개발자",
                required_count=2,
                position_status="OPEN",
            ),
        ]
    )
    db.commit()
    return project


def test_auth_012_withdrawal_verification_and_anonymization(
    client: TestClient, db_session: Session
) -> None:
    """비밀번호·활성 프로젝트 검증과 탈퇴 개인정보 익명화를 확인한다."""
    user = _user(db_session, "withdraw")
    profile = UserProfile(
        user_id=user.user_id, introduction="삭제할 자기소개", onboarding_completed=True
    )
    token = RefreshToken(
        user_id=user.user_id,
        token_hash="withdraw-refresh",
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    db_session.add_all([profile, token])
    db_session.commit()

    wrong = client.request(
        "DELETE",
        "/api/v1/users/me",
        headers=_headers(user),
        json={"confirmation": "WITHDRAW", "password": "WrongPassword1!"},
    )
    assert wrong.status_code == 401
    assert wrong.json()["code"] == "INVALID_CREDENTIALS"

    topic, tech, role = _references(db_session)
    owned = _project(db_session, user, topic, tech, role, "소유", 10)
    blocked = client.request(
        "DELETE",
        "/api/v1/users/me",
        headers=_headers(user),
        json={"confirmation": "WITHDRAW", "password": PASSWORD},
    )
    assert blocked.status_code == 400
    assert blocked.json()["code"] == "INVALID_STATE_TRANSITION"

    owned.project_status = "COMPLETED"
    db_session.commit()
    withdrawn = client.request(
        "DELETE",
        "/api/v1/users/me",
        headers=_headers(user),
        json={"confirmation": "WITHDRAW", "password": PASSWORD},
    )
    assert withdrawn.status_code == 204
    db_session.refresh(user)
    db_session.refresh(profile)
    db_session.refresh(token)
    assert user.user_status == "WITHDRAWN"
    assert user.email.startswith("withdrawn-")
    assert profile.introduction is None
    assert token.revoked_at is not None


def test_recommendation_home_and_refresh_flow(client: TestClient, db_session: Session) -> None:
    """개인화 추천·유사 프로젝트·홈 조합·새로고침 흐름을 검증한다."""
    user = _user(db_session, "recommend")
    owner = _user(db_session, "owner")
    topic, tech, role = _references(db_session)
    db_session.add_all(
        [
            UserProfile(
                user_id=user.user_id, preferred_work_type="ONLINE", onboarding_completed=True
            ),
            UserTopic(user_id=user.user_id, topic_id=topic.topic_id),
            UserTechStack(
                user_id=user.user_id,
                tech_stack_id=tech.tech_stack_id,
                proficiency_level="INTERMEDIATE",
            ),
            UserRole(user_id=user.user_id, role_id=role.role_id, priority=1),
        ]
    )
    db_session.commit()
    first = _project(db_session, owner, topic, tech, role, "첫 번째", 3)
    second = _project(db_session, owner, topic, tech, role, "두 번째", 7)

    recommended = client.get("/api/v1/recommendations/projects?size=1", headers=_headers(user))
    assert recommended.status_code == 200
    assert recommended.json()["data"]["fallback"] is False
    assert recommended.json()["data"]["items"][0]["finalScore"] == 1.0
    assert len(recommended.json()["data"]["items"][0]["reasons"]) == 3
    assert recommended.json()["meta"]["hasNext"] is True

    similar = client.get(f"/api/v1/projects/{first.project_id}/similar?size=6")
    assert similar.status_code == 200
    assert similar.json()["data"]["items"][0]["projectId"] == second.project_id

    home = client.get("/api/v1/home?sectionSize=1", headers=_headers(user))
    assert home.status_code == 200
    assert home.json()["data"]["profileSummary"]["onboardingCompleted"] is True
    assert len(home.json()["data"]["latestProjects"]) == 1
    assert len(home.json()["data"]["closingSoonProjects"]) == 1

    refreshed = client.post(
        "/api/v1/recommendations/projects/refresh", headers=_headers(user), json={"force": True}
    )
    assert refreshed.status_code == 202
    assert refreshed.json()["data"]["status"] == "QUEUED"
    assert db_session.query(RecommendationResult).filter_by(user_id=user.user_id).count() == 0


def test_recommendation_fallback_and_swagger(client: TestClient, db_session: Session) -> None:
    """온보딩 미완성 대체 추천과 5개 API Swagger 계약을 검증한다."""
    user = _user(db_session, "fallback")
    owner = _user(db_session, "fallback-owner")
    topic, tech, role = _references(db_session)
    _project(db_session, owner, topic, tech, role, "대체", 5)
    db_session.add(UserProfile(user_id=user.user_id, onboarding_completed=False))
    db_session.commit()

    response = client.get("/api/v1/recommendations/projects", headers=_headers(user))
    assert response.status_code == 200
    assert response.json()["data"]["fallback"] is True
    assert response.json()["data"]["fallbackReason"] == "ONBOARDING_INCOMPLETE"

    schema = client.get("/openapi.json").json()
    assert schema["paths"]["/api/v1/users/me"]["delete"]["operationId"] == "AUTH_012_withdraw"
    assert schema["paths"]["/api/v1/home"]["get"]["operationId"] == "HOME_001"
    assert schema["paths"]["/api/v1/recommendations/projects"]["get"]["operationId"] == "RECO_001"
    assert (
        schema["paths"]["/api/v1/projects/{projectId}/similar"]["get"]["operationId"] == "RECO_002"
    )
    assert (
        schema["paths"]["/api/v1/recommendations/projects/refresh"]["post"]["operationId"]
        == "RECO_003"
    )
