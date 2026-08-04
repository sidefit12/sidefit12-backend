"""파일 업로드 및 삭제 API."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, Form, Header, Path, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import request_id_context
from app.domains.auth.dependencies import get_current_user
from app.domains.files.openapi import error_example as _error
from app.domains.files.openapi import response_example as _response
from app.domains.files.schemas import FileUploadResponse
from app.domains.files.service import FileService
from app.domains.users.models import User
from app.integrations.object_storage import ObjectStorage, get_object_storage

router = APIRouter(tags=["파일"])


@router.post(
    "/files",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="파일 업로드",
    description=(
        "프로필 이미지 또는 공개 자료를 검증하여 오브젝트 스토리지에 저장합니다. "
        "확장자, MIME 유형, 파일 시그니처를 모두 검사합니다."
    ),
    operation_id="FILE_001",
    responses={
        201: _response("파일 업로드 성공"),
        401: _error("인증 실패", "UNAUTHORIZED", "로그인이 필요합니다."),
        413: _error("파일 용량 초과", "FILE_TOO_LARGE", "파일 용량이 허용 범위를 초과했습니다."),
        415: _error(
            "지원하지 않는 파일", "UNSUPPORTED_MEDIA_TYPE", "지원하지 않는 파일 형식입니다."
        ),
        503: _error(
            "저장소 장애",
            "STORAGE_UNAVAILABLE",
            "파일 저장 서비스를 일시적으로 사용할 수 없습니다.",
        ),
    },
)
async def upload_file(
    file: Annotated[UploadFile, File(description="업로드할 프로필 이미지 또는 공개 자료 파일")],
    file_category: Annotated[
        Literal["PROFILE_IMAGE", "PUBLIC_MATERIAL"],
        Form(alias="fileCategory", description="파일 분류"),
    ],
    visibility: Annotated[
        Literal["PUBLIC", "PRIVATE"], Form(description="파일 공개 범위")
    ] = "PRIVATE",
    preview_allowed: Annotated[
        bool, Form(alias="previewAllowed", description="미리보기 허용 여부")
    ] = True,
    download_allowed: Annotated[
        bool, Form(alias="downloadAllowed", description="다운로드 허용 여부")
    ] = False,
    idempotency_key: Annotated[
        str | None,
        Header(alias="Idempotency-Key", max_length=255, description="중복 업로드 방지 키"),
    ] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: ObjectStorage = Depends(get_object_storage),
):
    """인증 사용자의 파일을 업로드한다."""
    maximum = FileService.RULES[file_category]["maximum"]
    content = await file.read(maximum + 1)
    data = FileService.upload(
        db,
        user,
        storage,
        filename=file.filename or "upload",
        declared_mime_type=file.content_type or "application/octet-stream",
        content=content,
        file_category=file_category,
        visibility=visibility,
        preview_allowed=preview_allowed,
        download_allowed=download_allowed,
        idempotency_key=idempotency_key,
    )
    return {"data": data, "requestId": request_id_context.get()}


@router.delete(
    "/files/{fileId}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="파일 삭제",
    description="본인이 업로드한 파일의 프로필 참조를 해제하고 소프트 삭제합니다.",
    operation_id="FILE_002",
    responses={
        204: _response("파일 삭제 성공"),
        401: _error("인증 실패", "UNAUTHORIZED", "로그인이 필요합니다."),
        403: _error(
            "파일 소유권 없음",
            "RESOURCE_OWNERSHIP_REQUIRED",
            "리소스 소유자만 처리할 수 있습니다.",
        ),
        404: _error("파일 없음", "FILE_NOT_FOUND", "파일을 찾을 수 없습니다."),
    },
)
def delete_file(
    file_id: int = Path(alias="fileId", ge=1, description="삭제할 파일 식별자"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: ObjectStorage = Depends(get_object_storage),
) -> Response:
    """인증 사용자의 파일을 삭제한다."""
    FileService.delete(db, user, storage, file_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
