# API 설계 규칙

> API 설계·검토 요청 시 반드시 적용. 상세 체크리스트 → `knowledge/decisions/api-design-conventions.md`

## 핵심 원칙 (5개)

- **상태 코드**: 생성 201+Location / 비동기 202+status_url / 삭제 204 / 검증실패 422 / 충돌 409
- **Envelope 필수**: 단일 `{"data":{}}` / 목록 `{"data":[],"meta":{cursor,has_more,limit}}`
- **에러 포맷**: `{status, code, message, detail, instance, trace_id}` — 6개 필드 전부
- **에러 코드**: `{도메인}_{에러유형}` — AUTH / SPACE / NODE / PIPELINE / VALIDATION
- **페이지네이션**: cursor 기반 (`?limit=20&after=<cursor>`) — offset 금지

## 트리거

API 명세 작성·검토 시 → `knowledge/decisions/api-design-conventions.md` 읽기
