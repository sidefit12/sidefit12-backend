"""애플리케이션 구조화 로그와 요청 식별자를 설정하는 모듈."""

import json
import logging
import logging.config
import time
from contextvars import ContextVar, Token
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from starlette.types import ASGIApp, Message, Receive, Scope, Send

request_id_context: ContextVar[str] = ContextVar("request_id", default="-")


class JsonFormatter(logging.Formatter):
    """표준 LogRecord를 한 줄 JSON 로그로 변환한다."""

    def format(self, record: logging.LogRecord) -> str:
        """로그의 공통 필드와 이벤트별 추가 필드를 JSON으로 직렬화한다."""
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_context.get(),
        }
        for field in (
            "event",
            "method",
            "path",
            "status_code",
            "duration_ms",
            "user_id",
            "verification_id",
            "reference_id",
            "verification_type",
            "error_code",
        ):
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(level: str = "INFO") -> None:
    """콘솔에 출력되는 애플리케이션 구조화 로그를 초기화한다."""
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {"json": {"()": JsonFormatter}},
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                    "stream": "ext://sys.stdout",
                }
            },
            "root": {"handlers": ["console"], "level": level.upper()},
        }
    )


class RequestLoggingMiddleware:
    """HTTP 요청마다 식별자를 부여하고 처리 결과와 소요 시간을 기록한다."""

    def __init__(self, app: ASGIApp) -> None:
        """감쌀 ASGI 애플리케이션을 저장한다."""
        self.app = app
        self.logger = logging.getLogger("sidefit.request")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """HTTP 요청을 처리하고 응답 헤더와 로그에 요청 식별자를 남긴다."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        request_id = (
            headers.get(b"x-request-id", b"").decode("utf-8", errors="ignore") or uuid4().hex
        )
        token: Token[str] = request_id_context.set(request_id)
        started_at = time.perf_counter()
        status_code = 500

        async def send_with_request_id(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                response_headers = list(message.get("headers", []))
                response_headers.append(
                    (b"x-request-id", request_id.encode("ascii", errors="ignore"))
                )
                message["headers"] = response_headers
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            self.logger.info(
                "HTTP 요청 처리 완료",
                extra={
                    "event": "http_request_completed",
                    "method": scope.get("method"),
                    "path": scope.get("path"),
                    "status_code": status_code,
                    "duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
                },
            )
            request_id_context.reset(token)
