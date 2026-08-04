"""Firebase Admin SDK 기반 FCM 푸시 발송 모듈."""

import base64
import json
from functools import lru_cache

import firebase_admin
from firebase_admin import credentials, messaging

from app.core.config import get_settings


@lru_cache
def get_firebase_app():
    """로컬 파일 또는 Base64 서비스 계정으로 Firebase 앱을 초기화한다."""
    settings = get_settings()
    if settings.firebase_credentials_base64:
        decoded = base64.b64decode(settings.firebase_credentials_base64).decode("utf-8")
        credential = credentials.Certificate(json.loads(decoded))
    elif settings.firebase_credentials_path:
        credential = credentials.Certificate(settings.firebase_credentials_path)
    else:
        return None
    options = {"projectId": settings.firebase_project_id} if settings.firebase_project_id else None
    return firebase_admin.initialize_app(credential, options=options, name="sidefit-fcm")


class FirebaseMessagingService:
    """사용자의 활성 FCM 등록 토큰으로 푸시 알림을 발송한다."""

    @staticmethod
    def send(
        tokens: list[str], *, title: str, body: str, data: dict[str, str]
    ) -> tuple[int, set[str]]:
        """최대 500개 토큰에 발송하고 등록 해제된 토큰을 반환한다."""
        app = get_firebase_app()
        if app is None or not tokens:
            return 0, set()
        success_count = 0
        invalid_tokens: set[str] = set()
        for start in range(0, len(tokens), 500):
            chunk = tokens[start : start + 500]
            response = messaging.send_each_for_multicast(
                messaging.MulticastMessage(
                    tokens=chunk,
                    notification=messaging.Notification(title=title, body=body),
                    data=data,
                ),
                app=app,
            )
            success_count += response.success_count
            for token, item in zip(chunk, response.responses, strict=True):
                if not item.success and isinstance(item.exception, messaging.UnregisteredError):
                    invalid_tokens.add(token)
        return success_count, invalid_tokens
