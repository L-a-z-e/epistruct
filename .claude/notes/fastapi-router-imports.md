---
date: 2026-06-04
tags: [fastapi, router, imports, python, hmac]
---

# FastAPI router.py 임포트 구성 요소 + 문법 포인트

## 핵심 개념

FastAPI router.py에서 쓰는 import들의 역할과, 파라미터 타입으로 값 출처를 자동 판단하는 FastAPI 문법.

## 상세 설명

### imports 한 줄 요약

```python
import hmac
```
Python 표준 라이브러리. 두 문자열을 타이밍 공격 없이 안전하게 비교하는 `compare_digest` 하나 때문에 씀.

```python
from fastapi import APIRouter, Depends, Header, status
```

| 이름 | 역할 |
|------|------|
| `APIRouter` | 엔드포인트 그룹. `prefix="/auth"` 붙여서 `/auth/webhook`이 됨 |
| `Depends` | 의존성 주입. `Depends(get_session)` → FastAPI가 자동으로 DB 세션 만들어서 넣어줌 |
| `Header` | 요청 헤더 값 추출. `x_webhook_secret: str = Header(None)` → `X-Webhook-Secret` 헤더를 읽음 |
| `status` | HTTP 상태 코드 상수. `status.HTTP_204_NO_CONTENT` = `204`. 숫자 직접 안 써도 됨 |

```python
from sqlalchemy.ext.asyncio import AsyncSession
```
비동기 DB 세션 타입. `Depends(get_session)`으로 주입받는 객체의 타입 힌트용.

### 파라미터 타입으로 값 출처 자동 판단

```python
@router.post("/webhook", status_code=status.HTTP_204_NO_CONTENT)
async def supabase_webhook(
    payload: SupabaseWebhookPayload,              # BaseModel 서브클래스 → request body
    x_webhook_secret: str | None = Header(None),  # Header(...) → HTTP 헤더
    session: AsyncSession = Depends(get_session), # Depends(...) → 의존성 주입
) -> None:
```

FastAPI가 파라미터 타입/기본값을 보고 어디서 값을 꺼낼지 자동 판단:
- `BaseModel` 서브클래스 → request body (JSON 자동 파싱)
- `Header(...)` → HTTP 헤더 (변수명 snake_case → 헤더명 kebab-case 자동 변환: `x_webhook_secret` → `X-Webhook-Secret`)
- `Depends(...)` → 의존성 주입 (DB 세션, 인증 등)
- 그 외 단순 타입 → query parameter

### `_` 접두사 관례

```python
def _verify_secret(received: str | None) -> bool:
    ...
```

`_` 접두사는 "이 파일 내부에서만 쓰는 함수"라는 Python 관례. 강제는 아니지만 `from module import *` 시 노출 안 됨. 외부에서 쓸 일 없는 헬퍼 함수에 붙임.

### `hmac.compare_digest` vs `==` — 타이밍 공격 방어

```python
# 위험
if received == settings.supabase_webhook_secret:
    ...

# 안전
hmac.compare_digest(received, settings.supabase_webhook_secret)
```

`==`는 앞 글자부터 비교하다 틀리면 바로 `False` 반환 → 응답 시간 차이로 비밀 값 길이/내용 유추 가능(타이밍 공격).

`compare_digest`는 항상 전체를 다 비교해서 시간이 일정 → 응답 시간으로 정보 유출 불가.

보안 관련 비교(시크릿, 토큰, 서명 등)는 항상 `hmac.compare_digest` 사용.

## 코드 예시

```python
# router.py 전체 구조
@router.post("/webhook", status_code=status.HTTP_204_NO_CONTENT)
async def supabase_webhook(
    payload: SupabaseWebhookPayload,
    x_webhook_secret: str | None = Header(None),
    session: AsyncSession = Depends(get_session),
) -> None:
    if not _verify_secret(x_webhook_secret):
        raise UnauthorizedError(message="Invalid webhook secret")
    ...

def _verify_secret(received: str | None) -> bool:
    if not settings.supabase_webhook_secret:
        return True  # 시크릿 미설정 시 개발 환경으로 간주
    if not received:
        return False
    return hmac.compare_digest(received, settings.supabase_webhook_secret)
```

## 관련 개념

- `fastapi-middleware.md` — FastAPI 요청/응답 파이프라인
- `pydantic-basics.md` — BaseModel, 타입 검증
- `webhook-explained.md` — Webhook 동작 흐름 전체
