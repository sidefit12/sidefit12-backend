"""Gemini 텍스트 임베딩 API 연동 모듈."""

import math

from google import genai
from google.genai import types

from app.core.config import get_settings


class GeminiEmbeddingService:
    """설정된 Gemini 모델로 추천용 텍스트 벡터를 생성한다."""

    @staticmethod
    def embed(text: str, *, task_type: str) -> list[float]:
        """텍스트를 설정된 차원의 정규화된 임베딩으로 변환한다."""
        settings = get_settings()
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY가 설정되지 않았습니다.")
        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.embed_content(
            model=settings.gemini_embedding_model,
            contents=text,
            config=types.EmbedContentConfig(
                task_type=task_type,
                output_dimensionality=settings.gemini_embedding_dimension,
            ),
        )
        if not response.embeddings or response.embeddings[0].values is None:
            raise RuntimeError("Gemini에서 임베딩 결과를 반환하지 않았습니다.")
        values = [float(value) for value in response.embeddings[0].values]
        if len(values) != settings.gemini_embedding_dimension:
            raise RuntimeError("Gemini 임베딩 차원이 설정값과 일치하지 않습니다.")
        if settings.gemini_embedding_model == "gemini-embedding-001":
            magnitude = math.sqrt(sum(value * value for value in values))
            if magnitude == 0:
                raise RuntimeError("크기가 0인 임베딩은 저장할 수 없습니다.")
            values = [value / magnitude for value in values]
        return values
