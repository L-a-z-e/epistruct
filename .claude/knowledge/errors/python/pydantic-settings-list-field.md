---
type: error
tech: python, pydantic-settings, fastapi
tags: [pydantic, BaseSettings, list, env, dotenv]
created: 2026-06-03
---

# pydantic-settings list 필드 .env 파싱 에러

## 증상

```
pydantic_settings.exceptions.SettingsError:
error parsing value for field "allowed_origins" from source "DotEnvSettingsSource"
Expecting value: line 1 column 1 (char 0)
```

서버 시작 시 즉시 crash. `list[str]` 타입 필드 관련.

## 원인

pydantic-settings는 `list[str]` 같은 복합 타입 필드를 .env에서 읽을 때 **JSON으로 파싱**하려 한다.

```env
# 이렇게 쓰면 에러 — JSON이 아님
ALLOWED_ORIGINS=http://localhost:8081,http://localhost:3000

# 이렇게 써야 함 — JSON 배열
ALLOWED_ORIGINS=["http://localhost:8081","http://localhost:3000"]
```

`env_list_delimiter` 설정은 일부 버전에서 동작하지 않는다. 가장 안정적인 방법은 JSON 배열 형식.

## 해결

1. `.env` 파일에서 해당 환경변수를 JSON 배열 형식으로 수정
2. `.env.example`도 동일하게 수정

```env
ALLOWED_ORIGINS=["http://localhost:8081","http://localhost:3000"]
```

## 예방

**`config.py`에서 `list[str]` 필드를 새로 추가할 때마다:**
→ `.env`와 `.env.example`에 JSON 배열 형식으로 추가

```python
# config.py
allowed_origins: list[str] = ["http://localhost:8081"]

# .env / .env.example
# ALLOWED_ORIGINS=["http://localhost:8081","http://localhost:3000"]
```

## 영향 범위

`BaseSettings`를 상속한 클래스의 모든 `list[*]`, `set[*]`, `dict[*]` 타입 필드에 동일하게 적용.
