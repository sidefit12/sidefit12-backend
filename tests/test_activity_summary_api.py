"""내 활동 요약 API 테스트."""

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.project_applications.models import ProjectApplication
from app.domains.project_bookmarks.models import ProjectBookmark
from app.domains.project_positions.models import ProjectPosition
from app.domains.projects.models import Project
from app.domains.roles.models import Role
from app.domains.users.models import User
from tests.conftest import SentEmailStore
from tests.test_auth_api import dispatch_and_confirm, signup


def _project(owner_user_id: int, title: str) -> Project:
    return Project(
        owner_user_id=owner_user_id,
        title=title,
        summary=f"{title} summary",
        description=f"{title} description",
        work_type="ONLINE",
        recruitment_deadline=datetime.now(timezone.utc) + timedelta(days=30),
        recruitment_status="RECRUITING",
        project_status="PREPARING",
        visibility="PUBLIC",
        moderation_status="VISIBLE",
    )


def test_activity_summary_counts(
    client: TestClient,
    db_session: Session,
    sent_emails: SentEmailStore,
) -> None:
    signup_data = signup(client, dispatch_and_confirm(client, sent_emails))
    headers = {"Authorization": f"Bearer {signup_data['accessToken']}"}
    user = db_session.scalar(select(User).where(User.email == "tester@example.com"))
    other = User(
        email="owner@example.com",
        password_hash="not-used",
        nickname="project-owner",
        user_status="ACTIVE",
        system_role="USER",
    )
    role = Role(role_code="BACKEND", role_name="백엔드 개발자")
    db_session.add_all([other, role])
    db_session.flush()

    authored = [_project(user.user_id, f"authored-{index}") for index in range(3)]
    others = [_project(other.user_id, f"other-{index}") for index in range(8)]
    db_session.add_all([*authored, *others])
    db_session.flush()

    positions = [
        ProjectPosition(
            project_id=project.project_id,
            role_id=role.role_id,
            position_title="Backend",
            required_count=1,
            position_status="OPEN",
        )
        for project in others[:3]
    ]
    db_session.add_all(positions)
    db_session.flush()
    db_session.add_all(
        [
            ProjectApplication(
                project_id=others[index].project_id,
                project_position_id=positions[index].project_position_id,
                applicant_user_id=user.user_id,
                application_message="지원합니다.",
                application_status="PENDING" if index < 2 else "ACCEPTED",
            )
            for index in range(3)
        ]
        + [
            ProjectBookmark(user_id=user.user_id, project_id=project.project_id)
            for project in others
        ]
    )
    db_session.commit()

    response = client.get("/api/v1/users/me/activity-summary", headers=headers)

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["data"] == {
        "authoredProjectCount": 3,
        "pendingApplicationCount": 2,
        "acceptedApplicationCount": 1,
        "bookmarkedProjectCount": 8,
    }
    assert response.json()["requestId"] != "-"


def test_activity_summary_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/users/me/activity-summary")

    assert response.status_code == 401
    assert response.json()["code"] == "AUTHENTICATION_REQUIRED"
