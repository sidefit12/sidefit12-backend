"""모집 자동 종료 스케줄 작업 실행 진입점."""

import json

from app.core.database import SessionLocal
from app.domains.internal_processing.service import InternalProcessingService


def main() -> int:
    """모집 자동 종료 작업을 실행하고 프로세스 종료 코드를 반환한다."""
    with SessionLocal() as db:
        result = InternalProcessingService.close_recruitment(db)
    print(json.dumps(result.model_dump(by_alias=True), ensure_ascii=False, default=str))
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
