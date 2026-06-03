---
date: 2026-06-03
tags: [python, pydantic, validation, fastapi, spring]
---

# Pydantic 기초

## 핵심 개념
Python 객체에 타입 검증을 자동으로 해주는 라이브러리. 타입 힌트를 런타임에 실제로 강제한다.

---

## 기본 동작

```python
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int
```

```python
# 올바른 데이터
user = User(name="Laze", age=30)      # OK

# 타입이 틀렸을 때
user = User(name="Laze", age="서른")  # ValidationError 발생!

# 자동 변환
user = User(name="Laze", age="30")    # "30" → 30 자동 변환 후 OK
```

---

## Epistruct에서 쓰이는 곳

### 1. BaseSettings (config.py) — .env 파일 읽기 + 타입 검증

```python
class Settings(BaseSettings):
    database_url: str              # 기본값 없음 → .env에 없으면 시작 시 즉시 에러
    app_env: str = "development"   # 기본값 있음 → .env에 없어도 OK
```

### 2. BaseModel (schemas.py) — HTTP 요청/응답 데이터 검증

```python
class CreateSpaceRequest(BaseModel):
    name: str
    is_public: bool = False
```

FastAPI가 HTTP 요청 body를 받으면 Pydantic이 자동으로 파싱·검증.
타입이 틀리면 422 응답을 자동으로 반환.

---

## Spring 비유

Spring의 `@Valid` + `@NotNull` + `@Size` 같은 Bean Validation을 클래스 선언만으로 처리.
별도 어노테이션 없이 타입 선언 자체가 검증 규칙.

```java
// Spring
public class CreateSpaceRequest {
    @NotNull
    private String name;
    private boolean isPublic = false;
}
```

```python
# Pydantic — 타입 선언이 곧 검증 규칙
class CreateSpaceRequest(BaseModel):
    name: str
    is_public: bool = False
```

---

## 관련 개념
- `BaseSettings` — pydantic-settings 패키지. .env 파일 자동 로드
- `SettingsConfigDict` — BaseSettings 동작 방식 설정 (env_file 경로 등)
- FastAPI 422 응답 — Pydantic 검증 실패 시 자동 반환
