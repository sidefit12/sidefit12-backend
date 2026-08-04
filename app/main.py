"""SideFit FastAPI 애플리케이션 생성 및 전역 설정 모듈."""

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.core.config import get_settings
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import RequestLoggingMiddleware, configure_logging
from app.domains.auth.openapi import apply_auth_openapi
from app.domains.auth.router import router as auth_router
from app.domains.files.openapi import apply_file_openapi
from app.domains.files.router import router as files_router
from app.domains.home.openapi import apply_home_openapi
from app.domains.home.router import router as home_router
from app.domains.notification_preferences.openapi import apply_notification_preference_openapi
from app.domains.notification_preferences.router import router as notification_preferences_router
from app.domains.notifications.openapi import apply_notification_openapi
from app.domains.notifications.router import router as notifications_router
from app.domains.project_applications.openapi import apply_application_openapi
from app.domains.project_applications.router import router as applications_router
from app.domains.project_bookmarks.openapi import apply_bookmark_openapi
from app.domains.project_bookmarks.router import router as bookmarks_router
from app.domains.project_collaboration_channels.openapi import apply_channel_openapi
from app.domains.project_collaboration_channels.router import router as channels_router
from app.domains.project_members.openapi import apply_member_openapi
from app.domains.project_members.router import router as members_router
from app.domains.project_reviews.openapi import apply_review_openapi
from app.domains.project_reviews.router import router as reviews_router
from app.domains.projects.openapi import apply_project_openapi
from app.domains.projects.router import router as projects_router
from app.domains.recommendations.openapi import apply_recommendation_openapi
from app.domains.recommendations.router import router as recommendations_router
from app.domains.reference_data.openapi import apply_reference_data_openapi
from app.domains.reference_data.router import router as reference_data_router
from app.domains.reports.admin_router import router as admin_reports_router
from app.domains.reports.openapi import apply_report_openapi
from app.domains.reports.router import router as reports_router
from app.domains.user_profiles.openapi import apply_profile_openapi
from app.domains.users.router import router as users_router

settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(
    title="SideFit API",
    description="SideFit 백엔드 API 서버",
    version="0.1.0",
)

app.add_middleware(RequestLoggingMiddleware)
app.include_router(users_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(files_router, prefix="/api/v1")
app.include_router(home_router, prefix="/api/v1")
app.include_router(recommendations_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")
app.include_router(notification_preferences_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")
app.include_router(applications_router, prefix="/api/v1")
app.include_router(bookmarks_router, prefix="/api/v1")
app.include_router(members_router, prefix="/api/v1")
app.include_router(channels_router, prefix="/api/v1")
app.include_router(reviews_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")
app.include_router(admin_reports_router, prefix="/api/v1")
app.include_router(reference_data_router, prefix="/api/v1")
register_exception_handlers(app)


def custom_openapi():
    """API 명세서 기반 요청·응답 예시가 포함된 OpenAPI 문서를 생성한다."""
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title, version=app.version, description=app.description, routes=app.routes
    )
    schema = apply_auth_openapi(schema)
    schema = apply_file_openapi(schema)
    schema = apply_home_openapi(schema)
    schema = apply_recommendation_openapi(schema)
    schema = apply_notification_openapi(schema)
    schema = apply_notification_preference_openapi(schema)
    schema = apply_profile_openapi(schema)
    schema = apply_project_openapi(schema)
    schema = apply_application_openapi(schema)
    schema = apply_bookmark_openapi(schema)
    schema = apply_member_openapi(schema)
    schema = apply_channel_openapi(schema)
    schema = apply_review_openapi(schema)
    schema = apply_report_openapi(schema)
    app.openapi_schema = apply_reference_data_openapi(schema)
    return app.openapi_schema


app.openapi = custom_openapi
