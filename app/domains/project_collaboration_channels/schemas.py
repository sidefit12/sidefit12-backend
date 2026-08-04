"""프로젝트 협업 채널 요청 및 응답 스키마."""

from typing import Literal

from pydantic import AnyUrl, BaseModel, ConfigDict, Field, field_validator

from app.domains.auth.schemas import to_camel

ChannelType = Literal["DISCORD", "KAKAO_OPEN_CHAT", "SLACK", "NOTION", "OTHER"]


class ChannelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


class ChannelCreateRequest(ChannelModel):
    channel_name: str = Field(
        min_length=1, max_length=100, description="협업 채널명", examples=["SideFit Discord"]
    )
    channel_type: ChannelType = Field(description="협업 채널 유형", examples=["DISCORD"])
    channel_url: AnyUrl = Field(
        max_length=2048, description="HTTPS 협업 채널 URL", examples=["https://discord.gg/example"]
    )

    @field_validator("channel_url")
    @classmethod
    def https_only(cls, value: AnyUrl):
        if value.scheme != "https":
            raise ValueError("협업 채널 URL은 HTTPS만 사용할 수 있습니다.")
        return value


class ChannelUpdateRequest(ChannelModel):
    channel_name: str | None = Field(None, min_length=1, max_length=100, description="협업 채널명")
    channel_type: ChannelType | None = Field(None, description="협업 채널 유형")
    channel_url: AnyUrl | None = Field(None, max_length=2048, description="HTTPS 협업 채널 URL")
    is_active: bool | None = Field(None, description="활성 여부")

    _https_only = field_validator("channel_url")(ChannelCreateRequest.https_only.__func__)


class ChannelResource(ChannelModel):
    channel_id: int = Field(
        validation_alias="project_collaboration_channel_id", description="협업 채널 식별자"
    )
    channel_name: str
    channel_type: ChannelType
    channel_url: str
    is_active: bool


class ChannelData(ChannelModel):
    items: list[ChannelResource]


class ChannelResponse(ChannelModel):
    success: bool = True
    data: ChannelResource
    request_id: str | None = None


class ChannelListResponse(ChannelModel):
    success: bool = True
    data: ChannelData
    request_id: str | None = None
