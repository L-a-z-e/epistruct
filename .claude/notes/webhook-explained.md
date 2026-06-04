---
date: 2026-06-04
tags: [webhook, supabase, fastapi, auth]
---

# Webhook 개념 + 이 프로젝트에서의 동작 흐름

## 핵심 개념

Webhook = "일 생기면 내가 너한테 HTTP로 알려줄게"

일반 API는 내가 먼저 물어보는 방식(폴링)이지만, webhook은 반대로 **Supabase가 먼저 우리 서버를 호출**한다.

## 상세 설명

### Supabase → 우리 서버 흐름

```
유저가 Supabase로 회원가입
        ↓
Supabase의 auth.users 테이블에 행 INSERT
        ↓
Supabase가 우리 서버로 HTTP POST 전송
POST https://우리서버.com/api/v1/auth/webhook
        ↓
우리 services.py의 handle_webhook("INSERT", record, None) 실행
        ↓
우리 PostgreSQL users 테이블에 행 생성
```

### 실제 Payload 예시

Supabase가 보내는 JSON:
```json
{
  "type": "INSERT",
  "table": "users",
  "schema": "auth",
  "record": {
    "id": "a1b2c3d4-...",
    "email": "laze@gmail.com",
    "raw_user_meta_data": {
      "display_name": "Laze"
    }
  },
  "old_record": null
}
```

`type`은 `"INSERT" / "UPDATE" / "DELETE"` 세 가지 — Supabase database webhook이 DB 변경 종류를 그대로 전달한다.

## 코드 예시

```python
# services.py
async def handle_webhook(self, event_type: str, record: dict, old_record: dict | None):
    user_id = uuid.UUID(record["id"])          # Supabase UUID 그대로 사용

    if event_type in ("INSERT", "UPDATE"):
        meta = record.get("raw_user_meta_data") or {}
        display_name = meta.get("display_name") or meta.get("name") or email.split("@")[0] or "User"
        await self._repo.upsert(User(id=user_id, display_name=display_name))

    elif event_type == "DELETE":
        await self._repo.soft_delete(user_id)  # deleted_at 기록, 물리 삭제 아님
```

## X-Webhook-Secret 헤더가 필요한 이유

webhook URL은 인터넷에 노출된다. 누구나 `POST /auth/webhook`을 보낼 수 있어서, Supabase가 보낸 요청인지 확인하는 비밀 값이 필요하다.

`.env`의 `SUPABASE_WEBHOOK_SECRET`을 헤더에 넣어서 보내도록 Supabase 설정에서 지정한다. 서버는 이 헤더 값이 일치하지 않으면 요청을 거부한다.

## 서버 다운 시 유실 문제

Supabase가 HTTP POST를 보내는데 응답이 없으면 → **재시도 없이 그냥 유실**.  
즉 유저가 가입했는데 우리 `users` 테이블에 행이 없는 상태가 될 수 있다.

### 대응 전략 비교

| 방법 | 방식 | 적합한 상황 |
|------|------|------------|
| **Lazy upsert** | API 첫 요청 시 users에 없으면 그때 생성 | 개발/초기 단계 ✅ |
| **Webhook 재시도 큐** | Redis/SQS로 실패한 webhook 재처리 | 운영 안정화 단계 |
| **Supabase Edge Function** | Supabase 내부에서 직접 DB 쓰기 | Supabase 종속 강해짐 |

현재 프로젝트는 **Lazy upsert 전략** 채택 — webhook으로 받으면 생성하고, 누락됐으면 인증 통과 시 users 테이블에 없을 경우 자동 생성하는 fallback 병행.

## 관련 개념

- `dependencies.py`의 `get_current_user` — lazy upsert fallback 포함
- `auth/services/services.py` — `handle_webhook`, `get_or_create`
- `SUPABASE_WEBHOOK_SECRET` — `.env` 환경변수
