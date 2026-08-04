"""FCM 푸시 기기 등록·삭제와 알림 발송 테스트."""

from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_token
from app.domains.notifications.service import NotificationService
from app.domains.push_devices.models import PushDevice
from app.domains.users.models import User
from app.integrations.firebase_messaging import FirebaseMessagingService


def _user(db: Session) -> User:
    user = User(
        email="push@sidefit.dev",
        password_hash="hash",
        nickname="푸시사용자",
        user_status="ACTIVE",
        system_role="USER",
    )
    db.add(user)
    db.commit()
    return user


def _header(user: User) -> dict[str, str]:
    token = create_token(user.user_id, token_type="access", expires_delta=timedelta(minutes=10))
    return {"Authorization": f"Bearer {token}"}


def test_push_device_registration_delivery_and_deletion(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    """FCM 토큰의 멱등 등록, 알림 발송 연계와 비활성화를 검증한다."""
    user = _user(db_session)
    token = "test-fcm-registration-token-1234567890"
    sent = []

    def fake_send(tokens, *, title, body, data):
        sent.append({"tokens": tokens, "title": title, "body": body, "data": data})
        return len(tokens), set()

    monkeypatch.setattr(FirebaseMessagingService, "send", fake_send)
    request = {"registrationToken": token, "platform": "WEB", "deviceName": "Chrome"}
    first = client.post("/api/v1/users/me/push-devices", headers=_header(user), json=request)
    repeated = client.post("/api/v1/users/me/push-devices", headers=_header(user), json=request)
    assert first.status_code == repeated.status_code == 200
    assert db_session.query(PushDevice).count() == 1

    assert NotificationService.application_received(db_session, user.user_id, 10)
    db_session.commit()
    assert sent[0]["tokens"] == [token]
    assert sent[0]["data"]["referenceId"] == "10"

    deleted = client.request(
        "DELETE",
        "/api/v1/users/me/push-devices",
        headers=_header(user),
        json={"registrationToken": token},
    )
    assert deleted.status_code == 200
    assert deleted.json()["data"]["deleted"] is True
    assert db_session.query(PushDevice).one().is_active is False


def test_push_device_swagger_has_korean_examples(client: TestClient) -> None:
    """푸시 기기 API의 한글 설명과 요청·응답 예시를 검증한다."""
    schema = client.get("/openapi.json").json()
    for method in ("post", "delete"):
        operation = schema["paths"]["/api/v1/users/me/push-devices"][method]
        assert operation["summary"]
        assert operation["description"]
        assert operation["requestBody"]["content"]["application/json"]["examples"]
        assert operation["responses"]["200"]["content"]["application/json"]["example"]
