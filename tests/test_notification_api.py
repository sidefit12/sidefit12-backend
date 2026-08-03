"""Excel API 명세서의 NOTI-001~006 알림 및 알림 설정 통합 테스트."""

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_token
from app.domains.notification_preferences.models import NotificationPreference
from app.domains.notifications.models import Notification
from app.domains.notifications.service import NotificationService
from app.domains.users.models import User


def _header(user: User) -> dict[str, str]:
    token = create_token(user.user_id, token_type="access", expires_delta=timedelta(minutes=10))
    return {"Authorization": f"Bearer {token}"}


def _users(db: Session) -> tuple[User, User]:
    user = User(
        email="notification-user@sidefit.dev",
        password_hash="hashed",
        nickname="알림 사용자",
        user_status="ACTIVE",
        system_role="USER",
    )
    other = User(
        email="notification-other@sidefit.dev",
        password_hash="hashed",
        nickname="다른 사용자",
        user_status="ACTIVE",
        system_role="USER",
    )
    db.add_all([user, other])
    db.commit()
    return user, other


def _notification(
    db: Session,
    user: User,
    *,
    notification_type: str,
    created_at: datetime,
    is_read: bool = False,
) -> Notification:
    item = Notification(
        user_id=user.user_id,
        notification_type=notification_type,
        title="테스트 알림",
        content="알림 API 동작을 검증합니다.",
        reference_type="PROJECT",
        reference_id=100,
        is_read=is_read,
        read_at=created_at if is_read else None,
        created_at=created_at,
    )
    db.add(item)
    db.commit()
    return item


def test_notification_list_filter_unread_count_and_read(
    client: TestClient, db_session: Session
) -> None:
    """최신순 목록, 필터, 미읽음 수와 본인 알림 멱등 읽음 처리를 검증한다."""
    user, other = _users(db_session)
    now = datetime.now(timezone.utc)
    received = _notification(
        db_session,
        user,
        notification_type="APPLICATION_RECEIVED",
        created_at=now - timedelta(minutes=2),
    )
    accepted = _notification(
        db_session,
        user,
        notification_type="APPLICATION_ACCEPTED",
        created_at=now - timedelta(minutes=1),
    )
    other_item = _notification(
        db_session,
        other,
        notification_type="SYSTEM",
        created_at=now,
    )

    response = client.get(
        "/api/v1/notifications?isRead=false&notificationType=APPLICATION_ACCEPTED&page=0&size=20",
        headers=_header(user),
    )
    assert response.status_code == 200
    assert [item["notificationId"] for item in response.json()["data"]["items"]] == [
        accepted.notification_id
    ]
    assert response.json()["data"]["unreadCount"] == 2

    unread = client.get("/api/v1/notifications/unread-count", headers=_header(user))
    assert unread.status_code == 200
    assert unread.json()["data"]["unreadCount"] == 2

    read = client.patch(
        f"/api/v1/notifications/{received.notification_id}/read", headers=_header(user)
    )
    repeated = client.patch(
        f"/api/v1/notifications/{received.notification_id}/read", headers=_header(user)
    )
    assert read.status_code == repeated.status_code == 200
    assert repeated.json()["data"]["isRead"] is True
    assert repeated.json()["data"]["readAt"] == read.json()["data"]["readAt"]

    forbidden = client.patch(
        f"/api/v1/notifications/{other_item.notification_id}/read", headers=_header(user)
    )
    assert forbidden.status_code == 403
    missing = client.patch("/api/v1/notifications/999999/read", headers=_header(user))
    assert missing.status_code == 404


def test_read_all_uses_boundary_and_is_idempotent(client: TestClient, db_session: Session) -> None:
    """기준 시각 이전 알림만 일괄 읽음 처리하고 재요청을 멱등하게 처리한다."""
    user, _ = _users(db_session)
    now = datetime.now(timezone.utc)
    old = _notification(
        db_session,
        user,
        notification_type="MEMBER_LEFT",
        created_at=now - timedelta(hours=2),
    )
    recent = _notification(
        db_session,
        user,
        notification_type="MEMBER_JOINED",
        created_at=now - timedelta(minutes=10),
    )
    boundary = now - timedelta(hours=1)

    response = client.patch(
        "/api/v1/notifications/read-all",
        headers=_header(user),
        json={"before": boundary.isoformat()},
    )
    assert response.status_code == 200
    assert response.json()["data"] == {"unreadCount": 1, "updatedCount": 1}
    db_session.refresh(old)
    db_session.refresh(recent)
    assert old.is_read is True
    assert recent.is_read is False

    repeated = client.patch(
        "/api/v1/notifications/read-all",
        headers=_header(user),
        json={"before": boundary.isoformat()},
    )
    assert repeated.status_code == 200
    assert repeated.json()["data"] == {"unreadCount": 1, "updatedCount": 0}


def test_notification_preferences_and_generation_policy(
    client: TestClient, db_session: Session
) -> None:
    """기본 설정, 부분 수정, 필수 시스템 알림과 생성 시 설정 적용을 검증한다."""
    user, _ = _users(db_session)

    default = client.get("/api/v1/users/me/notification-preferences", headers=_header(user))
    assert default.status_code == 200
    assert default.json()["data"]["applicationEnabled"] is True
    assert default.json()["data"]["systemEnabled"] is True
    assert db_session.query(NotificationPreference).count() == 0

    updated = client.patch(
        "/api/v1/users/me/notification-preferences",
        headers=_header(user),
        json={"applicationEnabled": False, "teamEnabled": False},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["applicationEnabled"] is False
    assert updated.json()["data"]["teamEnabled"] is False
    assert updated.json()["data"]["systemEnabled"] is True

    disabled_system = client.patch(
        "/api/v1/users/me/notification-preferences",
        headers=_header(user),
        json={"systemEnabled": False},
    )
    assert disabled_system.status_code == 400
    empty = client.patch(
        "/api/v1/users/me/notification-preferences", headers=_header(user), json={}
    )
    assert empty.status_code == 400

    NotificationService.application_received(db_session, user.user_id, 200)
    NotificationService.team_member_changed(db_session, user.user_id, 100, event_type="REMOVED")
    db_session.commit()
    assert db_session.query(Notification).count() == 0


def test_notification_swagger_contract(client: TestClient) -> None:
    """NOTI-001~006의 한글 Swagger 설명과 요청·응답 예시를 검증한다."""
    schema = client.get("/openapi.json").json()
    operations = [
        ("/api/v1/notifications", "get", "NOTI_001"),
        ("/api/v1/notifications/unread-count", "get", "NOTI_002"),
        ("/api/v1/notifications/{notificationId}/read", "patch", "NOTI_003"),
        ("/api/v1/notifications/read-all", "patch", "NOTI_004"),
        ("/api/v1/users/me/notification-preferences", "get", "NOTI_005"),
        ("/api/v1/users/me/notification-preferences", "patch", "NOTI_006"),
    ]
    for path, method, operation_id in operations:
        operation = schema["paths"][path][method]
        assert operation["operationId"] == operation_id
        assert operation["summary"]
        assert operation["responses"]["200"]["content"]["application/json"]["example"]

    read_all = schema["paths"]["/api/v1/notifications/read-all"]["patch"]
    assert read_all["requestBody"]["content"]["application/json"]["examples"]["default"]["value"][
        "before"
    ]
    preference_fields = schema["components"]["schemas"]["NotificationPreferenceUpdateRequest"][
        "properties"
    ]
    assert "비활성화" in preference_fields["systemEnabled"]["description"]
