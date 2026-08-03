"""프로필 API의 Swagger 요청·응답 예시."""

from app.core.openapi import apply_examples

PROFILE = {
    "user": {
        "userId": 1,
        "email": "user@example.com",
        "nickname": "sidefitter",
        "userStatus": "ACTIVE",
        "systemRole": "USER",
        "onboardingCompleted": True,
        "profileImageUrl": None,
    },
    "introduction": "함께 성장하는 백엔드 개발자입니다.",
    "careerLevel": "JUNIOR",
    "preferredWorkType": "ONLINE",
    "preferredRegion": "서울",
    "availableStartDate": "2026-08-10",
    "availableEndDate": "2026-12-31",
    "availableHoursPerWeek": 10,
    "profileImageFileId": None,
    "publicMaterialFileId": None,
    "externalLinkUrl": "https://github.com/example",
    "topics": [],
    "techStacks": [],
    "roles": [],
}
REQUEST_EXAMPLES = {
    "PROFILE_002_save_onboarding": {
        "introduction": "함께 성장하는 백엔드 개발자입니다.",
        "preferredWorkType": "ONLINE",
        "preferredRegion": "서울",
        "availableStartDate": "2026-08-10",
        "availableEndDate": "2026-12-31",
        "availableHoursPerWeek": 10,
        "topicIds": [1, 3],
        "techStacks": [
            {
                "techStackId": 4,
                "proficiencyLevel": "INTERMEDIATE",
                "experienceMonths": 12,
                "isLearning": False,
            }
        ],
        "roles": [{"roleId": 2, "priority": 1, "experienceLevel": "BEGINNER"}],
    },
    "PROFILE_005_update_profile": {
        "nickname": "sidefitter",
        "introduction": "프로젝트를 찾고 있습니다.",
        "careerLevel": "JUNIOR",
        "preferredWorkType": "HYBRID",
        "preferredRegion": "서울",
        "availableHoursPerWeek": 10,
        "profileImageFileId": 10,
        "publicMaterialFileId": 11,
        "externalLinkUrl": "https://github.com/example",
    },
    "PROFILE_006_replace_topics": {"topicIds": [1, 3, 5]},
    "PROFILE_007_replace_tech_stacks": {
        "techStacks": [
            {
                "techStackId": 4,
                "proficiencyLevel": "INTERMEDIATE",
                "experienceMonths": 12,
                "isLearning": False,
            }
        ]
    },
    "PROFILE_008_replace_roles": {
        "roles": [{"roleId": 2, "priority": 1, "experienceLevel": "BEGINNER"}]
    },
}
SUCCESS_EXAMPLES = {
    "PROFILE_001_onboarding_options": {
        "success": True,
        "data": {
            "currentSelection": {"topicIds": [], "techStackIds": [], "roleIds": []},
            "topics": [
                {"topicId": 1, "topicCode": "FINTECH", "topicName": "핀테크", "isActive": True}
            ],
            "techStacks": [
                {
                    "techStackId": 4,
                    "techStackCode": "FASTAPI",
                    "techStackName": "FastAPI",
                    "category": "Backend",
                    "isActive": True,
                }
            ],
            "roles": [{"roleId": 2, "roleCode": "BACKEND", "roleName": "백엔드", "isActive": True}],
        },
    },
    "PROFILE_002_save_onboarding": {"success": True, "data": PROFILE},
    "PROFILE_003_my_profile": {"success": True, "data": PROFILE},
    "PROFILE_004_public_profile": {
        "success": True,
        "data": {
            "userId": 2,
            "nickname": "applicant",
            "introduction": "백엔드 개발자입니다.",
            "profileImageFileId": None,
            "publicMaterialFileId": None,
            "externalLinkUrl": "https://github.com/example",
            "topics": [],
            "techStacks": [],
            "roles": [],
        },
    },
    "PROFILE_005_update_profile": {"success": True, "data": PROFILE},
    "PROFILE_006_replace_topics": {
        "success": True,
        "data": {
            "topics": [
                {
                    "topicId": 1,
                    "topicCode": "FINTECH",
                    "topicName": "핀테크",
                    "isActive": True,
                    "interestLevel": 3,
                    "priority": 0,
                }
            ]
        },
    },
    "PROFILE_007_replace_tech_stacks": {
        "success": True,
        "data": {
            "techStacks": [
                {
                    "techStackId": 4,
                    "techStackCode": "FASTAPI",
                    "techStackName": "FastAPI",
                    "category": "Backend",
                    "isActive": True,
                    "proficiencyLevel": "INTERMEDIATE",
                    "experienceMonths": 12,
                    "isLearning": False,
                }
            ]
        },
    },
    "PROFILE_008_replace_roles": {
        "success": True,
        "data": {
            "roles": [
                {
                    "roleId": 2,
                    "roleCode": "BACKEND",
                    "roleName": "백엔드",
                    "isActive": True,
                    "priority": 1,
                    "experienceLevel": "BEGINNER",
                }
            ]
        },
    },
}
OPERATION_IDS = {
    f"PROFILE_{number:03d}_{suffix}"
    for number, suffix in [
        (1, "onboarding_options"),
        (2, "save_onboarding"),
        (3, "my_profile"),
        (4, "public_profile"),
        (5, "update_profile"),
        (6, "replace_topics"),
        (7, "replace_tech_stacks"),
        (8, "replace_roles"),
    ]
}


def apply_profile_openapi(schema: dict) -> dict:
    """프로필 API 예시를 OpenAPI 문서에 적용한다."""
    return apply_examples(
        schema,
        operation_ids=OPERATION_IDS,
        request_examples=REQUEST_EXAMPLES,
        success_examples=SUCCESS_EXAMPLES,
    )
