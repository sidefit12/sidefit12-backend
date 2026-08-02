"""애플리케이션 전역 예외 처리기를 정의하는 모듈."""

import logging

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppException


logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """애플리케이션에 전역 예외 처리기를 등록한다."""

    @app.exception_handler(AppException)
    async def handle_app_exception(
        request: Request,
        exception: AppException,
    ) -> JSONResponse:
        """애플리케이션 커스텀 예외를 공통 응답으로 변환한다."""

        logger.warning(
            "애플리케이션 예외가 발생했습니다.",
            extra={
                "event": "app_exception",
                "method": request.method,
                "path": request.url.path,
                "status_code": exception.status_code,
                "error_code": exception.code,
            },
        )
        return JSONResponse(
            status_code=exception.status_code,
            content=jsonable_encoder(
                {
                    "code": exception.code,
                    "message": exception.message,
                    "details": exception.details,
                }
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation_error(
        request: Request,
        exception: RequestValidationError,
    ) -> JSONResponse:
        """Pydantic 요청값 검증 오류를 처리한다."""

        logger.warning(
            "요청값 검증에 실패했습니다.",
            extra={
                "event": "request_validation_failed",
                "method": request.method,
                "path": request.url.path,
                "status_code": status.HTTP_400_BAD_REQUEST,
                "error_code": "VALIDATION_ERROR",
            },
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=jsonable_encoder(
                {
                    "code": "VALIDATION_ERROR",
                    "message": "요청값이 올바르지 않습니다.",
                    "details": exception.errors(),
                }
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(
        _request: Request,
        exception: StarletteHTTPException,
    ) -> JSONResponse:
        """FastAPI와 Starlette의 HTTP 예외를 처리한다."""

        message = (
            exception.detail
            if isinstance(exception.detail, str)
            else "요청 처리 중 오류가 발생했습니다."
        )

        return JSONResponse(
            status_code=exception.status_code,
            content=jsonable_encoder(
                {
                    "code": f"HTTP_{exception.status_code}",
                    "message": message,
                    "details": (None if isinstance(exception.detail, str) else exception.detail),
                }
            ),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(
        request: Request,
        exception: Exception,
    ) -> JSONResponse:
        """처리되지 않은 서버 예외를 처리한다."""

        logger.error(
            "처리되지 않은 예외가 발생했습니다. method=%s path=%s",
            request.method,
            request.url.path,
            exc_info=exception,
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "code": "INTERNAL_SERVER_ERROR",
                "message": "서버 내부 오류가 발생했습니다.",
                "details": None,
            },
        )
