"""푸시 기기 등록·삭제 API 스키마."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.domains.auth.schemas import to_camel


class PushDeviceModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class PushDeviceRegisterRequest(PushDeviceModel):
    registration_token: str = Field(min_length=20, max_length=2048, description="FCM 등록 토큰")
    platform: Literal["WEB", "ANDROID", "IOS"] = Field(description="푸시 기기 플랫폼")
    device_name: str | None = Field(None, min_length=1, max_length=100, description="기기 표시명")


class PushDeviceDeleteRequest(PushDeviceModel):
    registration_token: str = Field(
        min_length=20, max_length=2048, description="삭제할 FCM 등록 토큰"
    )


class PushDeviceData(PushDeviceModel):
    push_device_id: int
    platform: str
    device_name: str | None = None
    is_active: bool


class PushDeviceResponse(PushDeviceModel):
    success: bool = True
    data: PushDeviceData
    request_id: str | None = None


class PushDeviceDeleteData(PushDeviceModel):
    deleted: bool


class PushDeviceDeleteResponse(PushDeviceModel):
    success: bool = True
    data: PushDeviceDeleteData
    request_id: str | None = None
