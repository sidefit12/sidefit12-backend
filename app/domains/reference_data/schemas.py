"""기준정보 API 응답 스키마."""

from pydantic import BaseModel, ConfigDict, Field

from app.domains.auth.schemas import to_camel


class ReferenceDataModel(BaseModel):
    """기준정보 API에서 사용하는 공통 Pydantic 모델."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


class TopicItem(ReferenceDataModel):
    topic_id: int = Field(description="토픽 식별자", examples=[1])
    topic_code: str = Field(description="토픽 코드", examples=["FINTECH"])
    topic_name: str = Field(description="토픽명", examples=["핀테크"])
    is_active: bool = Field(description="활성 여부", examples=[True])


class TechStackItem(ReferenceDataModel):
    tech_stack_id: int = Field(description="기술 스택 식별자", examples=[1])
    tech_stack_code: str = Field(description="기술 스택 코드", examples=["JAVA"])
    tech_stack_name: str = Field(description="기술 스택명", examples=["Java"])
    category: str | None = Field(description="기술 스택 분류", examples=["언어"])
    is_active: bool = Field(description="활성 여부", examples=[True])


class RoleItem(ReferenceDataModel):
    role_id: int = Field(description="역할 식별자", examples=[1])
    role_code: str = Field(description="역할 코드", examples=["BACKEND"])
    role_name: str = Field(description="역할명", examples=["백엔드 개발자"])
    is_active: bool = Field(description="활성 여부", examples=[True])


class TopicListData(ReferenceDataModel):
    items: list[TopicItem] = Field(description="토픽 목록")


class TechStackListData(ReferenceDataModel):
    items: list[TechStackItem] = Field(description="기술 스택 목록")


class RoleListData(ReferenceDataModel):
    items: list[RoleItem] = Field(description="역할 목록")


class TopicListResponse(ReferenceDataModel):
    success: bool = Field(description="요청 성공 여부", examples=[True])
    data: TopicListData = Field(description="토픽 목록 응답 데이터")
    request_id: str | None = Field(default=None, description="요청 추적 식별자")


class TechStackListResponse(ReferenceDataModel):
    success: bool = Field(description="요청 성공 여부", examples=[True])
    data: TechStackListData = Field(description="기술 스택 목록 응답 데이터")
    request_id: str | None = Field(default=None, description="요청 추적 식별자")


class RoleListResponse(ReferenceDataModel):
    success: bool = Field(description="요청 성공 여부", examples=[True])
    data: RoleListData = Field(description="역할 목록 응답 데이터")
    request_id: str | None = Field(default=None, description="요청 추적 식별자")
