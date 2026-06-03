# API 설계 규칙

> Epistruct API 명세 작성·검토 시 반드시 적용한다.
> 결정 근거: `knowledge/decisions/api-design-conventions.md`
> 전체 명세: `docs/design/api-spec.md`

---

## 명세 작성 체크리스트

API 엔드포인트를 작성하거나 검토할 때 아래 항목을 순서대로 확인한다.

### 1. 엔드포인트 구조

모든 엔드포인트는 아래 4가지를 포함해야 한다:
- HTTP 메서드 + URL
- Request (body / query params / path params 구분 명시)
- Response + HTTP 상태 코드
- **에러 케이스 표** `(상황 | code | HTTP)` — 누락 시 명세 미완성

### 2. HTTP 상태 코드 결정 기준

| 상황 | 올바른 코드 | 자주 틀리는 코드 |
|------|-----------|----------------|
| 리소스 생성 성공 | **201** + `Location` 헤더 필수 | 200 (틀림) |
| 비동기 작업 접수 | **202** + `status_url` + `estimated_seconds` | 200/201 (틀림) |
| 삭제·성공 반환 없음 | **204** (body 없음) | 200 (틀림) |
| JSON 파싱 실패 | **400** | 422 (틀림) |
| 입력값 검증 실패 | **422** | 400 (틀림) |
| 리소스 상태 충돌 | **409** | 422 (틀림) |
| 권한 없음 | **403** | 401 (틀림) |
| JWT 없음/만료 | **401** | 403 (틀림) |

**400 vs 422 구분**: JSON 자체를 파싱 못 하면 400. 파싱은 됐는데 값이 잘못됐으면 422.
**409 vs 422 구분**: 리소스의 현재 상태와 충돌하면 409. 입력값 자체가 나쁘면 422.

### 3. 응답 Envelope

모든 REST 응답은 Envelope 사용. 리소스를 직접 반환하지 않는다.

```
단일 리소스:  {"data": {...}}
목록:        {"data": [...], "meta": {"cursor": ..., "has_more": ..., "limit": ...}}
202 Accepted: {"data": {"job_id": ..., "status_url": ..., "estimated_seconds": ...}}
에러:         {"status": ..., "code": ..., "message": ..., "detail": ..., "instance": ..., "trace_id": ...}
```

### 4. 에러 코드 네이밍

`{도메인}_{에러유형}` 형식. 도메인은 아래 중 하나:

| 도메인 | 대상 |
|--------|------|
| `AUTH` | 인증/토큰/사용자 |
| `SPACE` | Space 리소스 |
| `GROUP` | 그룹/멤버 |
| `NODE` | 노드 (GraphQL errors 배열에서 사용) |
| `PIPELINE` | AI 파이프라인/Job |
| `VALIDATION` | 입력값 검증 |
| `RATE_LIMIT` | Rate limiting |

예: `SPACE_NOT_FOUND`, `GROUP_ROLE_INSUFFICIENT`, `PIPELINE_FILE_TOO_LARGE`

### 5. 날짜 형식

모든 날짜 필드는 **ISO 8601 + UTC** 사용.
```
올바름:  "created_at": "2026-06-02T09:00:00Z"
금지:    Unix timestamp 단독, 타임존 없는 로컬 시간
```

### 6. 페이지네이션

목록 엔드포인트는 **Cursor 기반** 사용. offset/page 기반 금지.
```
쿼리: ?limit=20&after=<cursor>
응답 meta: {"cursor": "...", "has_more": true, "limit": 20}
```

### 7. GraphQL 에러

GraphQL 에러는 HTTP 200 + `errors` 배열. `extensions`에 `code`, `status`, `trace_id` 포함.

---

## 검증 플로우

명세 작성 완료 후 아래 순서로 검토한다.

```
1. 모든 엔드포인트에 에러 케이스 표가 있는가?
2. 201 응답에 Location 헤더가 명시됐는가?
3. 202 응답에 status_url과 estimated_seconds가 있는가?
4. 에러 응답이 {status, code, message, detail, instance, trace_id} 형식인가?
5. 에러 코드가 {도메인}_{에러유형} 규칙을 따르는가?
6. 날짜 필드가 ISO 8601 UTC 형식인가?
7. 목록 응답에 cursor 페이지네이션 meta가 있는가?
8. 단일 리소스 응답도 {"data": {...}} Envelope를 쓰는가?
9. 400/422/409 구분이 올바른가?
```

→ 하나라도 미충족 시 해당 엔드포인트 수정 후 재검토.
