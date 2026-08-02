"""PROFILE-001~008 사용자 프로필 API 통합 테스트."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domains.roles.models import Role
from app.domains.tech_stacks.models import TechStack
from app.domains.topics.models import Topic
from tests.conftest import SentEmailStore
from tests.test_auth_api import dispatch_and_confirm, signup


def _authorization(client: TestClient, sent_emails: SentEmailStore) -> dict[str, str]:
    """테스트 사용자를 가입시키고 Bearer 인증 헤더를 반환한다."""
    data = signup(client, dispatch_and_confirm(client, sent_emails))
    return {"Authorization": f"Bearer {data['accessToken']}"}


def _seed_options(db: Session) -> tuple[Topic, Topic, TechStack, TechStack, Role, Role]:
    """온보딩에서 선택할 활성 기준정보를 저장한다."""
    values = (
        Topic(topic_code="WEB", topic_name="웹 서비스"),
        Topic(topic_code="AI", topic_name="인공지능"),
        TechStack(tech_stack_code="PYTHON", tech_stack_name="Python", category="BACKEND"),
        TechStack(tech_stack_code="FASTAPI", tech_stack_name="FastAPI", category="BACKEND"),
        Role(role_code="BACKEND", role_name="백엔드 개발자"),
        Role(role_code="PM", role_name="프로덕트 매니저"),
    )
    db.add_all(values)
    db.commit()
    return values


def test_profile_001_to_008_flow(
    client: TestClient,
    db_session: Session,
    sent_emails: SentEmailStore,
) -> None:
    """온보딩 선택지 조회부터 세부 관심정보 교체까지 전체 흐름을 검증한다."""
    topic1, topic2, tech1, tech2, role1, role2 = _seed_options(db_session)
    headers = _authorization(client, sent_emails)

    options = client.get("/api/v1/onboarding/options", headers=headers)
    assert options.status_code == 200
    assert len(options.json()["data"]["topics"]) == 2
    assert options.json()["data"]["currentSelection"]["topicIds"] == []

    onboarding = client.put(
        "/api/v1/users/me/onboarding",
        headers=headers,
        json={
            "introduction": "함께 성장하는 개발자입니다.",
            "careerLevel": "JUNIOR",
            "preferredWorkType": "HYBRID",
            "preferredRegion": "서울",
            "availableHoursPerWeek": 20,
            "topicIds": [topic1.topic_id],
            "techStacks": [
                {
                    "techStackId": tech1.tech_stack_id,
                    "proficiencyLevel": "INTERMEDIATE",
                    "experienceMonths": 18,
                    "isLearning": False,
                }
            ],
            "roles": [
                {
                    "roleId": role1.role_id,
                    "priority": 1,
                    "experienceLevel": "INTERMEDIATE",
                }
            ],
        },
    )
    assert onboarding.status_code == 200
    assert onboarding.json()["data"]["user"]["onboardingCompleted"] is True

    mine = client.get("/api/v1/users/me/profile", headers=headers)
    assert mine.status_code == 200
    user_id = mine.json()["data"]["user"]["userId"]
    assert mine.json()["data"]["user"]["email"] == "tester@example.com"

    public = client.get(f"/api/v1/users/{user_id}/profile", headers=headers)
    assert public.status_code == 200
    assert "email" not in public.json()["data"]

    updated = client.patch(
        "/api/v1/users/me/profile",
        headers=headers,
        json={
            "nickname": "profileuser",
            "introduction": "<b>안전한 소개</b>",
            "externalLinkUrl": "https://github.com/sidefit",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["introduction"] == "안전한 소개"
    assert updated.json()["data"]["externalLinkUrl"] == "https://github.com/sidefit"

    topics = client.put(
        "/api/v1/users/me/topics",
        headers=headers,
        json={"topicIds": [topic2.topic_id]},
    )
    assert topics.status_code == 200
    assert topics.json()["data"]["topics"][0]["topicCode"] == "AI"

    tech_stacks = client.put(
        "/api/v1/users/me/tech-stacks",
        headers=headers,
        json={
            "techStacks": [
                {
                    "techStackId": tech2.tech_stack_id,
                    "proficiencyLevel": "LEARNING",
                    "experienceMonths": 1,
                    "isLearning": True,
                }
            ]
        },
    )
    assert tech_stacks.status_code == 200
    assert tech_stacks.json()["data"]["techStacks"][0]["techStackCode"] == "FASTAPI"

    roles = client.put(
        "/api/v1/users/me/roles",
        headers=headers,
        json={"roles": [{"roleId": role2.role_id, "priority": 1, "experienceLevel": "BEGINNER"}]},
    )
    assert roles.status_code == 200
    assert roles.json()["data"]["roles"][0]["roleCode"] == "PM"


def test_inactive_profile_option_is_rejected(
    client: TestClient,
    db_session: Session,
    sent_emails: SentEmailStore,
) -> None:
    """비활성 기준정보를 프로필에 저장하지 못하도록 검증한다."""
    inactive = Topic(topic_code="INACTIVE", topic_name="비활성", is_active=False)
    db_session.add(inactive)
    db_session.commit()
    headers = _authorization(client, sent_emails)

    response = client.put(
        "/api/v1/users/me/topics",
        headers=headers,
        json={"topicIds": [inactive.topic_id]},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "INVALID_PROFILE_SELECTION"


def test_profile_api_requires_authentication(client: TestClient) -> None:
    """프로필 API가 인증되지 않은 요청을 거절하는지 검증한다."""
    response = client.get("/api/v1/onboarding/options")
    assert response.status_code == 401
    assert response.json()["code"] == "AUTHENTICATION_REQUIRED"
