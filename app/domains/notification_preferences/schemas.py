"""사용자 알림 수신 설정 API 요청·응답 스키마."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domains.auth.schemas import to_camel


class NotificationPreferenceModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


class NotificationPreferenceUpdateRequest(NotificationPreferenceModel):
    application_enabled: bool | None = Field(default=None, description="지원 알림 수신 여부")
    recruitment_deadline_enabled: bool | None = Field(
        default=None, description="모집 마감 알림 수신 여부"
    )
    team_enabled: bool | None = Field(default=None, description="팀 알림 수신 여부")
    system_enabled: bool | None = Field(
        default=None, description="필수 시스템 알림 수신 여부이며 비활성화할 수 없습니다."
    )

    @model_validator(mode="after")
    def validate_update(self):
        if not self.model_fields_set:
            raise ValueError("최소 한 개의 알림 설정을 입력해야 합니다.")
        if self.system_enabled is False:
            raise ValueError("필수 시스템 알림은 비활성화할 수 없습니다.")
        return self


class NotificationPreferenceData(NotificationPreferenceModel):
    application_enabled: bool
    recruitment_deadline_enabled: bool
    team_enabled: bool
    system_enabled: bool
    updated_at: datetime


class NotificationPreferenceResponse(NotificationPreferenceModel):
    success: bool = True
    data: NotificationPreferenceData
    request_id: str | None = None
