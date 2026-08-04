"""추천 API Swagger 예시."""

from app.core.openapi import apply_examples

PROJECT = {
    "projectId": 100,
    "title": "AI 자산관리 프로젝트",
    "summary": "개인화 자산관리 서비스",
    "workType": "ONLINE",
    "region": None,
    "recruitmentDeadline": "2026-08-31T14:59:59Z",
    "recruitmentStatus": "RECRUITING",
    "projectStatus": "PREPARING",
    "viewCount": 120,
    "createdAt": "2026-08-01T10:00:00Z",
    "owner": {"userId": 1, "nickname": "leader"},
    "topics": [],
    "techStacks": [],
    "positions": [],
    "isApplied": False,
    "isBookmarked": True,
}
ITEM = {
    "recommendationResultId": 500,
    "project": PROJECT,
    "ruleScore": 0.7,
    "semanticScore": None,
    "finalScore": 0.7,
    "recommendationVersion": "rule-v1",
    "reasons": [
        {
            "reasonType": "MATCHED_ROLE",
            "reasonText": "희망 역할과 일치하는 포지션을 모집하고 있어요.",
            "contributionScore": 0.4,
        }
    ],
}


def apply_recommendation_openapi(schema: dict) -> dict:
    """추천 API 요청·응답 예시를 적용한다."""
    return apply_examples(
        schema,
        operation_ids={"RECO_001", "RECO_002", "RECO_003"},
        request_examples={"RECO_003": {"force": False}},
        success_examples={
            "RECO_001": {
                "success": True,
                "data": {"items": [ITEM], "fallback": False, "fallbackReason": None},
                "meta": {"nextCursor": None, "hasNext": False},
            },
            "RECO_002": {"success": True, "data": {"items": [PROJECT]}},
            "RECO_003": {"success": True, "data": {"jobId": "job_01HXYZ", "status": "QUEUED"}},
        },
    )
