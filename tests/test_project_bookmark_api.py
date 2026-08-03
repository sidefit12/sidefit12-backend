"""Excel API 명세서의 BOOKMARK-001~003 프로젝트 북마크 통합 테스트."""

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_token
from app.domains.project_bookmarks.models import ProjectBookmark
from app.domains.project_positions.models import ProjectPosition
from app.domains.projects.models import Project
from app.domains.roles.models import Role
from app.domains.users.models import User


def _header(user: User) -> dict[str, str]:
    token = create_token(user.user_id, token_type="access", expires_delta=timedelta(minutes=10))
    return {"Authorization": f"Bearer {token}"}


def _seed_user(db: Session) -> tuple[User, User, Role]:
    owner = User(
        email="bookmark-owner@sidefit.dev",
        password_hash="hashed",
        nickname="북마크 프로젝트장",
        user_status="ACTIVE",
        system_role="USER",
    )
    user = User(
        email="bookmark-user@sidefit.dev",
        password_hash="hashed",
        nickname="북마크 사용자",
        user_status="ACTIVE",
        system_role="USER",
    )
    role = Role(role_code="BOOKMARK_BACKEND", role_name="북마크 백엔드")
    db.add_all([owner, user, role])
    db.commit()
    return owner, user, role


def _project(
    db: Session,
    owner: User,
    role: Role,
    *,
    title: str,
    recruitment_status: str = "RECRUITING",
    visibility: str = "PUBLIC",
) -> Project:
    project = Project(
        owner_user_id=owner.user_id,
        title=title,
        summary=f"{title}의 북마크 목록 동작을 검증합니다.",
        description=f"{title} 프로젝트의 상세 설명입니다.",
        work_type="ONLINE",
        recruitment_deadline=datetime.now(timezone.utc) + timedelta(days=10),
        recruitment_status=recruitment_status,
        project_status="PREPARING",
        visibility=visibility,
    )
    db.add(project)
    db.flush()
    db.add(
        ProjectPosition(
            project_id=project.project_id,
            role_id=role.role_id,
            position_title="백엔드 개발자",
            required_count=2,
            position_status="OPEN" if recruitment_status == "RECRUITING" else "CLOSED",
        )
    )
    db.commit()
    return project


def test_bookmark_put_delete_are_idempotent(client: TestClient, db_session: Session) -> None:
    """북마크 등록과 해제가 중복 요청에도 동일한 성공 상태를 반환하는지 검증한다."""
    owner, user, role = _seed_user(db_session)
    project = _project(db_session, owner, role, title="멱등 북마크 프로젝트")

    first = client.put(f"/api/v1/projects/{project.project_id}/bookmark", headers=_header(user))
    repeated = client.put(f"/api/v1/projects/{project.project_id}/bookmark", headers=_header(user))
    assert first.status_code == repeated.status_code == 200
    assert repeated.json()["data"] == {"projectId": project.project_id, "bookmarked": True}
    assert db_session.query(ProjectBookmark).count() == 1

    removed = client.delete(
        f"/api/v1/projects/{project.project_id}/bookmark", headers=_header(user)
    )
    removed_again = client.delete(
        f"/api/v1/projects/{project.project_id}/bookmark", headers=_header(user)
    )
    assert removed.status_code == removed_again.status_code == 200
    assert removed_again.json()["data"] == {
        "projectId": project.project_id,
        "bookmarked": False,
    }
    assert db_session.query(ProjectBookmark).count() == 0


def test_bookmark_list_filters_closed_deleted_and_private_projects(
    client: TestClient, db_session: Session
) -> None:
    """최신순 목록, 마감 필터와 삭제·비공개 프로젝트 제외 규칙을 검증한다."""
    owner, user, role = _seed_user(db_session)
    recruiting = _project(db_session, owner, role, title="모집 중 프로젝트")
    closed = _project(
        db_session,
        owner,
        role,
        title="모집 마감 프로젝트",
        recruitment_status="CLOSED",
    )
    deleted = _project(db_session, owner, role, title="삭제 프로젝트")
    private = _project(db_session, owner, role, title="비공개 프로젝트", visibility="PRIVATE")

    for project in (recruiting, closed, deleted):
        response = client.put(
            f"/api/v1/projects/{project.project_id}/bookmark", headers=_header(user)
        )
        assert response.status_code == 200
    private_response = client.put(
        f"/api/v1/projects/{private.project_id}/bookmark", headers=_header(user)
    )
    assert private_response.status_code == 404

    deleted.deleted_at = datetime.now(timezone.utc)
    deleted.deletion_reason = "북마크 삭제 글 제외 동작을 검증합니다."
    db_session.commit()

    all_items = client.get("/api/v1/users/me/bookmarks", headers=_header(user))
    assert all_items.status_code == 200
    assert [item["projectId"] for item in all_items.json()["data"]["items"]] == [
        closed.project_id,
        recruiting.project_id,
    ]
    assert all(item["isBookmarked"] is True for item in all_items.json()["data"]["items"])

    recruiting_only = client.get(
        "/api/v1/users/me/bookmarks?includeClosed=false&page=0&size=20",
        headers=_header(user),
    )
    assert recruiting_only.status_code == 200
    assert [item["projectId"] for item in recruiting_only.json()["data"]["items"]] == [
        recruiting.project_id
    ]
    assert recruiting_only.json()["meta"] == {
        "page": 0,
        "size": 20,
        "totalElements": 1,
        "totalPages": 1,
        "hasNext": False,
    }


def test_bookmark_auth_not_found_and_swagger(client: TestClient, db_session: Session) -> None:
    """북마크 인증·프로젝트 없음 오류와 BOOKMARK-001~003 Swagger 계약을 검증한다."""
    owner, user, role = _seed_user(db_session)
    project = _project(db_session, owner, role, title="Swagger 북마크 프로젝트")

    assert client.put(f"/api/v1/projects/{project.project_id}/bookmark").status_code == 401
    not_found = client.put("/api/v1/projects/999999/bookmark", headers=_header(user))
    assert not_found.status_code == 404
    assert not_found.json()["code"] == "PROJECT_NOT_FOUND"

    schema = client.get("/openapi.json").json()
    operations = [
        ("/api/v1/projects/{projectId}/bookmark", "put", "BOOKMARK_001"),
        ("/api/v1/projects/{projectId}/bookmark", "delete", "BOOKMARK_002"),
        ("/api/v1/users/me/bookmarks", "get", "BOOKMARK_003"),
    ]
    for path, method, operation_id in operations:
        operation = schema["paths"][path][method]
        assert operation["operationId"] == operation_id
        assert operation["summary"]
        assert operation["responses"]["200"]["content"]["application/json"]["example"]
    parameters = schema["paths"]["/api/v1/users/me/bookmarks"]["get"]["parameters"]
    include_closed = next(item for item in parameters if item["name"] == "includeClosed")
    assert include_closed["description"] == "모집 마감 프로젝트 포함 여부"
