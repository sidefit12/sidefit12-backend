"""Maileroo Email API를 호출하는 이메일 발송 모듈."""

from collections.abc import Mapping
import base64
from datetime import datetime
import logging
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import httpx

from app.core.config import get_settings
from app.domains.auth.exceptions import EmailDeliveryUnavailableError


logger = logging.getLogger(__name__)


class MailerooEmailService:
    """Maileroo를 통해 HTML 또는 일반 텍스트 이메일을 발송하는 서비스."""

    def __init__(self, client: httpx.Client | None = None) -> None:
        """Maileroo 설정을 로드하고 HTTP client를 준비한다."""
        self.settings = get_settings()
        self.client = client or httpx.Client(timeout=10.0)

    def send_email(
        self,
        *,
        to_email: str,
        subject: str,
        html: str | None = None,
        plain: str | None = None,
        to_name: str | None = None,
        tags: Mapping[str, str] | None = None,
        attachments: list[dict[str, Any]] | None = None,
    ) -> str:
        """Maileroo에 이메일 발송을 요청하고 참조 ID를 반환한다.

        Args:
            to_email: 수신자 이메일 주소.
            subject: 이메일 제목.
            html: HTML 본문. plain과 둘 중 하나 이상 필수.
            plain: 일반 텍스트 본문. html과 둘 중 하나 이상 필수.
            to_name: 수신자 표시 이름.
            tags: Maileroo 발송 추적용 태그.
            attachments: Maileroo 첨부파일 목록.

        Returns:
            Maileroo가 반환한 이메일 참조 ID.

        Raises:
            EmailDeliveryUnavailableError: Maileroo 요청 실패 또는 발송 실패.
        """
        if not html and not plain:
            raise ValueError("html or plain email content is required")

        recipient: dict[str, str] = {"address": to_email}
        if to_name:
            recipient["display_name"] = to_name

        payload: dict[str, Any] = {
            "from": {
                "address": self.settings.maileroo_from_email,
                "display_name": self.settings.maileroo_from_name,
            },
            "to": [recipient],
            "subject": subject,
        }
        if html is not None:
            payload["html"] = html
        if plain is not None:
            payload["plain"] = plain
        if tags:
            payload["tags"] = dict(tags)
        if attachments:
            payload["attachments"] = attachments

        try:
            response = self.client.post(
                self.settings.maileroo_api_url,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "X-Api-Key": self.settings.maileroo_api_key,
                },
                json=payload,
            )
            response.raise_for_status()
            response_data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.error(
                "Maileroo 이메일 발송 요청에 실패했습니다.",
                extra={"event": "maileroo_request_failed"},
                exc_info=exc,
            )
            raise EmailDeliveryUnavailableError() from exc

        if not response_data.get("success"):
            logger.error(
                "Maileroo가 이메일 발송 실패를 반환했습니다.",
                extra={"event": "maileroo_delivery_failed"},
            )
            raise EmailDeliveryUnavailableError()

        reference_id = response_data.get("data", {}).get("reference_id")
        if not reference_id:
            logger.error(
                "Maileroo 응답에 참조 ID가 없습니다.", extra={"event": "maileroo_reference_missing"}
            )
            raise EmailDeliveryUnavailableError()
        logger.info(
            "Maileroo 이메일 발송 요청이 완료되었습니다.",
            extra={"event": "maileroo_delivery_succeeded", "reference_id": reference_id},
        )
        return reference_id

    def send_verification_code(self, *, to_email: str, code: str) -> str:
        """이메일 인증 코드를 Maileroo로 발송한다."""
        html = self._render_verification_template(code=code)
        return self.send_email(
            to_email=to_email,
            subject="SideFit 이메일 인증 코드",
            html=html,
            plain=f"SideFit 이메일 인증 코드: {code}\n인증 코드는 5분 동안 유효합니다.",
            tags={"type": "email-verification"},
            attachments=[self._logo_attachment()],
        )

    def send_password_reset(self, *, to_email: str, reset_token: str) -> str:
        """일회용 비밀번호 재설정 링크를 Maileroo로 발송한다."""
        separator = "&" if "?" in self.settings.frontend_password_reset_url else "?"
        reset_url = (
            f"{self.settings.frontend_password_reset_url}{separator}"
            f"{urlencode({'token': reset_token})}"
        )
        html = self._render_password_reset_template(reset_url=reset_url)
        return self.send_email(
            to_email=to_email,
            subject="SideFit 비밀번호 재설정",
            html=html,
            plain=(
                f"SideFit 비밀번호 재설정 링크입니다.\n{reset_url}\n이 링크는 10분 동안 유효합니다."
            ),
            tags={"type": "password-reset"},
            attachments=[self._logo_attachment()],
        )

    @staticmethod
    def _render_verification_template(*, code: str, expires_in_minutes: int = 5) -> str:
        """인증 코드와 만료 시간을 HTML 템플릿에 삽입한다."""
        template_path = Path(__file__).parent / "templates" / "email_verification.html"
        template = template_path.read_text(encoding="utf-8")
        return (
            template.replace("{{ verification_code }}", code)
            .replace("{{ expires_in_minutes }}", str(expires_in_minutes))
            .replace("{{ current_year }}", str(datetime.now().year))
        )

    @staticmethod
    def _render_password_reset_template(*, reset_url: str, expires_in_minutes: int = 10) -> str:
        """재설정 URL과 만료 시간을 HTML 템플릿에 삽입한다."""
        template_path = Path(__file__).parent / "templates" / "password_reset.html"
        template = template_path.read_text(encoding="utf-8")
        return (
            template.replace("{{ reset_url }}", reset_url)
            .replace("{{ expires_in_minutes }}", str(expires_in_minutes))
            .replace("{{ current_year }}", str(datetime.now().year))
        )

    @staticmethod
    def _logo_attachment() -> dict[str, Any]:
        """HTML 메일에서 사용할 SideFit inline 로고 첨부 정보를 생성한다."""
        logo_path = Path(__file__).parent / "templates" / "sidefit-logo.png"
        return {
            "file_name": "sidefit-logo.png",
            "content_type": "image/png",
            "content": base64.b64encode(logo_path.read_bytes()).decode("ascii"),
            "inline": True,
        }

    def close(self) -> None:
        """서비스가 생성한 HTTP client의 연결을 종료한다."""
        self.client.close()
