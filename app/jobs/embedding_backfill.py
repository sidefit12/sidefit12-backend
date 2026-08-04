"""기존 사용자·프로젝트 임베딩 일괄 백필 실행 진입점."""

import argparse
import json

from app.core.database import SessionLocal
from app.domains.internal_processing.embedding_backfill_service import EmbeddingBackfillService


def main() -> int:
    """명령행 옵션에 따라 임베딩 백필을 실행하고 종료 코드를 반환한다."""
    parser = argparse.ArgumentParser(description="SideFit 추천 임베딩 일괄 백필")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="한 번에 조회할 사용자·프로젝트 수(기본값: 50, 최대: 500)",
    )
    args = parser.parse_args()
    with SessionLocal() as db:
        result = EmbeddingBackfillService.run(db, batch_size=args.batch_size)
    print(json.dumps(result.model_dump(by_alias=True), ensure_ascii=False))
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
