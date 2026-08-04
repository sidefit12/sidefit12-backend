"""프로젝트 협업 채널 Swagger 예시."""

from app.core.openapi import apply_examples

CHANNEL = {
    "channelId": 701,
    "channelName": "SideFit Discord",
    "channelType": "DISCORD",
    "channelUrl": "https://discord.gg/example",
    "isActive": True,
}
LIST = {"success": True, "data": {"items": [CHANNEL]}, "requestId": "req_01HXYZ"}
ONE = {"success": True, "data": CHANNEL, "requestId": "req_01HXYZ"}
CREATE = {
    "channelName": "SideFit Discord",
    "channelType": "DISCORD",
    "channelUrl": "https://discord.gg/example",
}
UPDATE = {
    "channelName": "SideFit Slack",
    "channelType": "SLACK",
    "channelUrl": "https://sidefit.slack.com",
    "isActive": True,
}


def response_example(description, example):
    return {"description": description, "content": {"application/json": {"example": example}}}


def error_example(description, code, message):
    return response_example(description, {"code": code, "message": message, "details": None})


def apply_channel_openapi(schema: dict) -> dict:
    return apply_examples(
        schema,
        operation_ids={"CHANNEL_001", "CHANNEL_002", "CHANNEL_003", "CHANNEL_004"},
        request_examples={"CHANNEL_002": CREATE, "CHANNEL_003": UPDATE},
        success_examples={"CHANNEL_001": LIST, "CHANNEL_002": ONE, "CHANNEL_003": ONE},
    )
