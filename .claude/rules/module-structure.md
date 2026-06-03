# 모듈 디렉토리 구조 규칙

## 확정 패턴

모든 모듈(`auth`, `knowledge`, `space`, `ai_pipeline`)은 아래 구조를 따른다.

```
{module}/
  domain/           # 엔티티, 인터페이스(추상), 이벤트, 값 객체
  services/         # 유스케이스 조율 (application 레이어 역할)
  repositories/     # SQLAlchemy 모델 + DB 구현체 + 외부 DB 연동
  router.py         # FastAPI APIRouter — HTTP 진입점
  schemas.py        # Pydantic 요청/응답 모델
  dependencies.py   # FastAPI Depends() 주입 정의
  gateway.py        # 타 모듈 호출 인터페이스 (모듈 간 통신)
```

`ai_pipeline` 모듈만 추가로 `adapters/` 폴더를 가진다:

```
ai_pipeline/
  ...
  adapters/
    extractors/     # URL, PDF, YouTube 텍스트 추출
    llm/            # Claude API 클라이언트
```

## 절대 금지 명칭

아래 명칭은 이 프로젝트에서 사용하지 않는다:

| 금지 | 대신 사용 |
|------|----------|
| `application/` | `services/` |
| `infrastructure/` | `repositories/` (DB) 또는 `adapters/` (외부 서비스) |
| `presentation/` | 플랫 파일로 — `router.py`, `schemas.py`, `dependencies.py` |

## 각 레이어 역할 요약

**domain/**
- 비즈니스 규칙과 엔티티 정의
- DB, HTTP, 외부 서비스에 의존하지 않는 순수 Python
- 다른 레이어가 이 레이어에 의존 (역방향 금지)

**services/**
- 유스케이스 단위로 로직 조율
- domain 객체를 조립하고 repositories를 호출
- HTTP 요청/응답 형식(Pydantic 스키마)을 직접 다루지 않음

**repositories/**
- SQLAlchemy ORM 모델 (`models.py`)
- domain/repositories.py 인터페이스의 실제 구현체
- DB 쿼리 외 비즈니스 로직 금지

**router.py / schemas.py / dependencies.py**
- router: URL 라우팅 + services 호출
- schemas: HTTP 요청/응답 전용 Pydantic 모델 (domain 엔티티와 분리)
- dependencies: JWT 검증, 권한 확인 등 FastAPI Depends() 정의
