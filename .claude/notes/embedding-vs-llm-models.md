---
date: 2026-06-03
tags: [embedding, llm, pgvector, vector, rag, ai]
---

# 생성 모델(LLM)과 임베딩 모델의 차이

## 핵심 개념
LLM(생성)과 임베딩 모델은 역할이 완전히 다르다. 여러 LLM을 지원해도 임베딩 모델은 하나로 고정해야 한다.

## 역할 차이

| | 생성 모델 (LLM) | 임베딩 모델 |
|--|----------------|------------|
| 역할 | 텍스트 생성·답변 | 텍스트 → 숫자 벡터 변환 |
| 예 | Claude, GPT-4, Gemini | text-embedding-3-small, voyage-3 |
| 교체 | 자유롭게 가능 | DB 전체 재임베딩 필요 |
| DB 저장 | 저장 안 함 | Vector 컬럼에 저장 |

## Perplexity 같은 서비스가 여러 LLM을 지원하는 원리

"Claude로 답변받기", "GPT-4로 답변받기"는 **생성 모델**을 바꾸는 것.
벡터 검색(RAG)용 임베딩 모델은 내부에서 하나로 고정돼 있다.

흐름:
1. 질문 입력 → 임베딩 모델로 벡터화 (고정)
2. pgvector로 유사 문서 검색 (고정)
3. 검색 결과 + 질문 → 선택한 LLM으로 답변 생성 (교체 가능)

마지막 단계에서만 LLM이 바뀌는 것. 임베딩은 항상 동일.

## Vector(1536) — 차원 수의 의미

임베딩 모델마다 출력 차원 수가 고정돼 있다:

| 모델 | 차원 수 |
|------|---------|
| OpenAI `text-embedding-3-small` | 1536 |
| OpenAI `text-embedding-ada-002` | 1536 |
| Voyage AI `voyage-3` | 1024 |
| Google `text-embedding-004` | 768 |

DB 컬럼 크기와 모델 출력 크기가 다르면 저장 불가. 반드시 일치해야 한다.

다른 모델의 벡터끼리는 유사도 비교가 의미없다:
```
"안녕" → OpenAI: [0.12, -0.34, ...]   ← 다른 벡터 공간
"안녕" → Voyage: [0.87, 0.21, ...]    ← 섞으면 틀린 결과
```

## embedding_model 컬럼 패턴

어떤 모델로 생성했는지 기록해 두면 나중에 모델 교체 시 추적 가능:

```python
embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)
embedding_model: Mapped[str | None] = mapped_column(String, nullable=True)
# 예: "openai/text-embedding-3-small", "voyage/voyage-3"
```

모델을 바꿀 때는 전체 재임베딩 + 마이그레이션 필요. 어떤 설계로도 피할 수 없음.

## 관련 개념
- pgvector, RAG, SQLAlchemy Vector 타입, 임베딩 생성 파이프라인
