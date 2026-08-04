"""Excel API 명세서의 FILE-001~002 파일 API 통합 테스트."""

from dataclasses import dataclass, field
from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_token
from app.domains.files.models import File
from app.domains.user_profiles.models import UserProfile
from app.domains.users.models import User
from app.integrations.object_storage import get_object_storage
from app.main import app


@dataclass
class MemoryStorage:
    """외부 S3 호출 없이 업로드와 삭제를 검증하는 저장소."""

    objects: dict[str, tuple[bytes, str]] = field(default_factory=dict)

    def upload(self, key: str, content: bytes, content_type: str) -> None:
        self.objects[key] = (content, content_type)

    def delete(self, key: str) -> None:
        self.objects.pop(key, None)

    def url(self, key: str, *, public: bool) -> str:
        kind = "public" if public else "signed"
        return f"https://storage.sidefit.test/{kind}/{key}"


def _user(db: Session, suffix: str) -> User:
    user = User(
        email=f"file-{suffix}@sidefit.dev",
        password_hash="hashed",
        nickname=f"파일사용자{suffix}",
        user_status="ACTIVE",
        system_role="USER",
    )
    db.add(user)
    db.commit()
    return user


def _header(user: User) -> dict[str, str]:
    token = create_token(user.user_id, token_type="access", expires_delta=timedelta(minutes=10))
    return {"Authorization": f"Bearer {token}"}


def _storage() -> MemoryStorage:
    storage = MemoryStorage()
    app.dependency_overrides[get_object_storage] = lambda: storage
    return storage


def test_file_upload_idempotency_and_profile_reference(
    client: TestClient, db_session: Session
) -> None:
    """파일 업로드, 멱등 재요청과 프로필 파일 연결을 검증한다."""
    storage = _storage()
    user = _user(db_session, "upload")
    headers = {**_header(user), "Idempotency-Key": "file-upload-001"}
    png = b"\x89PNG\r\n\x1a\n" + b"sidefit-image"
    multipart = {
        "fileCategory": "PROFILE_IMAGE",
        "visibility": "PRIVATE",
        "previewAllowed": "true",
        "downloadAllowed": "false",
    }
    files = {"file": ("avatar.png", png, "image/png")}

    uploaded = client.post("/api/v1/files", headers=headers, data=multipart, files=files)
    repeated = client.post("/api/v1/files", headers=headers, data=multipart, files=files)

    assert uploaded.status_code == 201
    assert repeated.status_code == 201
    resource = uploaded.json()["data"]["file"]
    assert repeated.json()["data"]["file"]["fileId"] == resource["fileId"]
    assert resource["mimeType"] == "image/png"
    assert resource["url"].startswith("https://storage.sidefit.test/signed/")
    assert len(storage.objects) == 1
    assert db_session.query(File).count() == 1

    profile = client.patch(
        "/api/v1/users/me/profile",
        headers=_header(user),
        json={"profileImageFileId": resource["fileId"]},
    )
    assert profile.status_code == 200
    assert profile.json()["data"]["profileImageFileId"] == resource["fileId"]


def test_file_validation_and_ownership(client: TestClient, db_session: Session) -> None:
    """파일 형식·공개 정책과 삭제 소유권 검증을 확인한다."""
    _storage()
    owner = _user(db_session, "owner")
    other = _user(db_session, "other")

    invalid_type = client.post(
        "/api/v1/files",
        headers=_header(owner),
        data={"fileCategory": "PROFILE_IMAGE"},
        files={"file": ("avatar.png", b"not-an-image", "image/png")},
    )
    assert invalid_type.status_code == 415
    assert invalid_type.json()["code"] == "UNSUPPORTED_MEDIA_TYPE"

    invalid_policy = client.post(
        "/api/v1/files",
        headers=_header(owner),
        data={
            "fileCategory": "PUBLIC_MATERIAL",
            "visibility": "PRIVATE",
            "downloadAllowed": "true",
        },
        files={"file": ("portfolio.pdf", b"%PDF-sidefit", "application/pdf")},
    )
    assert invalid_policy.status_code == 400
    assert invalid_policy.json()["code"] == "INVALID_DOWNLOAD_POLICY"

    uploaded = client.post(
        "/api/v1/files",
        headers=_header(owner),
        data={"fileCategory": "PUBLIC_MATERIAL", "visibility": "PUBLIC"},
        files={"file": ("portfolio.pdf", b"%PDF-sidefit", "application/pdf")},
    )
    file_id = uploaded.json()["data"]["file"]["fileId"]
    denied = client.delete(f"/api/v1/files/{file_id}", headers=_header(other))
    assert denied.status_code == 403
    assert denied.json()["code"] == "RESOURCE_OWNERSHIP_REQUIRED"


def test_file_delete_is_idempotent_and_detaches_profile(
    client: TestClient, db_session: Session
) -> None:
    """삭제 시 프로필 참조 해제와 소프트 삭제 및 멱등성을 검증한다."""
    storage = _storage()
    user = _user(db_session, "delete")
    uploaded = client.post(
        "/api/v1/files",
        headers=_header(user),
        data={"fileCategory": "PROFILE_IMAGE"},
        files={
            "file": (
                "avatar.webp",
                b"RIFF\x00\x00\x00\x00WEBPsidefit",
                "image/webp",
            )
        },
    )
    file_id = uploaded.json()["data"]["file"]["fileId"]
    profile = UserProfile(user_id=user.user_id, profile_image_file_id=file_id)
    db_session.add(profile)
    db_session.commit()

    deleted = client.delete(f"/api/v1/files/{file_id}", headers=_header(user))
    repeated = client.delete(f"/api/v1/files/{file_id}", headers=_header(user))

    assert deleted.status_code == 204
    assert repeated.status_code == 204
    db_session.refresh(profile)
    saved = db_session.get(File, file_id)
    assert profile.profile_image_file_id is None
    assert saved.file_status == "DELETED"
    assert saved.deleted_at is not None
    assert storage.objects == {}


def test_file_swagger_contract(client: TestClient) -> None:
    """파일 API의 multipart 필드와 한글 Swagger 예시를 검증한다."""
    schema = client.get("/openapi.json").json()
    upload = schema["paths"]["/api/v1/files"]["post"]
    delete = schema["paths"]["/api/v1/files/{fileId}"]["delete"]
    body_schema = upload["requestBody"]["content"]["multipart/form-data"]["schema"]
    component = schema["components"]["schemas"][body_schema["$ref"].split("/")[-1]]

    assert upload["operationId"] == "FILE_001"
    assert delete["operationId"] == "FILE_002"
    assert component["properties"]["file"]["description"].startswith("업로드할")
    assert component["properties"]["fileCategory"]["description"] == "파일 분류"
    assert upload["responses"]["201"]["content"]["application/json"]["example"]["data"]
    assert "본문" not in delete["responses"]["204"].get("content", {})
