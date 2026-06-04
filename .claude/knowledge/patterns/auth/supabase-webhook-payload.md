# Supabase Database Webhook Payload 패턴

## 이벤트별 payload 구조

INSERT/UPDATE와 DELETE는 `record` / `old_record` 위치가 다르다.

```json
// INSERT
{
  "type": "INSERT",
  "record": { "id": "...", "email": "...", "raw_user_meta_data": {} },
  "old_record": null
}

// UPDATE
{
  "type": "UPDATE",
  "record": { "id": "...", "email": "...", "raw_user_meta_data": {} },
  "old_record": { "id": "...", "email": "..." }
}

// DELETE — record가 null, old_record에 삭제된 데이터
{
  "type": "DELETE",
  "record": null,
  "old_record": { "id": "...", "email": "...", "raw_user_meta_data": {} }
}
```

## 핵심 규칙

- **DELETE 이벤트**: `record`는 항상 `null`. user_id는 반드시 `old_record`에서 꺼낸다.
- `record is None` early return을 DELETE 전에 넣으면 soft delete가 실행되지 않는다.

## 올바른 처리 패턴

```python
# router.py
if payload.type == "DELETE":
    if payload.old_record is None:
        return
    record_data = payload.old_record.model_dump()   # ← old_record 사용
else:
    if payload.record is None:
        return
    record_data = payload.record.model_dump()

await service.handle_webhook(payload.type, record_data, old)
```

## 잘못된 패턴 (버그)

```python
# ❌ DELETE 시 old_record를 처리하지 못하고 early return
if payload.record is None:
    return
await service.handle_webhook(payload.type, payload.record.model_dump(), ...)
```

## Supabase 설정

- Supabase Dashboard → Database → Webhooks → auth.users 테이블 대상
- Custom Headers에 `X-Webhook-Secret: {secret}` 추가
- 서버에서 `hmac.compare_digest`로 타이밍 공격 방어 검증
