# Epistruct API 명세

> 작성일: 2026-06-02
> 적용 버전: Phase 1-A
> 관련 문서: [ERD](./erd-ddd.md), [PRD v0.7](../prd/Epistruct_PRD_v0.7.md)

---

## 설계 원칙

| 원칙 | 내용 |
|------|------|
| REST | 단순 CRUD, 인증, Space/Group 관리 |
| GraphQL | Knowledge 그래프 조회 및 변경 (다중 리소스 조합 쿼리) |
| Polling 기본 | AI 파이프라인 비동기 작업 — HTTP 202 + job_id + GET 폴링 |
| SSE 선택적 | LLM 노드 추출 진행 상황 스트리밍 (텍스트 점진 출력) |
| gRPC 인터페이스 | 모듈 간 계약 — Phase 1은 함수 호출로 구현, MSA 전환 시 교체 |

---

## 공통 규격

### 엔드포인트 구조

```
/api/v1/**          REST — auth, space, ai_pipeline
/graphql            GraphQL — knowledge 모듈 전용
/internal/**        내부 전용 (외부 노출 금지, breaking change 자유)
```

### 인증

모든 `/api/v1/` 및 `/graphql` 요청에 Supabase JWT 필수.

```
Authorization: Bearer <supabase_jwt>
```

예외: `POST /api/v1/auth/webhook` (Supabase 내부 호출, `X-Supabase-Webhook-Secret`으로 검증)

### 공통 요청 헤더

| 헤더 | 필수 | 설명 |
|------|------|------|
| `Authorization` | 필수 | `Bearer <jwt>` |
| `Content-Type` | 필수 (body 있는 요청) | `application/json` 또는 `multipart/form-data` |
| `X-Request-ID` | 선택 | 클라이언트가 생성한 추적 ID. 없으면 서버가 생성. 에러 디버깅에 사용 |

### 공통 응답 헤더

```
X-Request-ID: req-7f3a9abc    ← 요청 추적 ID (클라이언트 전달값 또는 서버 생성)
```

---

## HTTP 상태 코드 결정 트리

```
요청 처리 결과
│
├─ 성공
│  ├─ 리소스 반환 / 수정 완료        → 200 OK
│  ├─ 리소스 생성                   → 201 Created  (+Location 헤더)
│  ├─ 비동기 작업 접수               → 202 Accepted (+status_url, estimated_seconds)
│  └─ 성공, 반환 없음 (DELETE 등)    → 204 No Content
│
├─ 클라이언트 에러
│  ├─ JSON 파싱 실패, 타입 불일치    → 400 Bad Request
│  ├─ JWT 없음 또는 만료             → 401 Unauthorized
│  ├─ 권한 없음                     → 403 Forbidden
│  ├─ 리소스 없음                   → 404 Not Found
│  ├─ 지원하지 않는 HTTP 메서드      → 405 Method Not Allowed
│  ├─ 비즈니스 규칙 충돌             → 409 Conflict
│  │  (예: 이미 존재하는 멤버, 이미 confirmed된 노드에 재확정 시도)
│  ├─ 입력 형식은 맞지만 값 검증 실패 → 422 Unprocessable Entity
│  │  (예: required 필드 누락, enum 범위 초과, 유효하지 않은 UUID)
│  └─ Rate limit 초과               → 429 Too Many Requests (+Retry-After 헤더)
│
└─ 서버 에러
   ├─ 서버 내부 오류                → 500 Internal Server Error
   ├─ 업스트림 서비스 실패           → 502 Bad Gateway
   │  (예: LLM API 오류, Supabase 연결 실패)
   ├─ 서비스 과부하 / 점검 중        → 503 Service Unavailable (+Retry-After 헤더)
   └─ 업스트림 타임아웃              → 504 Gateway Timeout
```

**400 vs 422 구분:**
- `400`: 요청 자체를 파싱할 수 없는 경우 (JSON 문법 오류, Content-Type 불일치)
- `422`: JSON은 유효하지만 값이 잘못된 경우 (필수 필드 누락, 허용되지 않는 값)

**409 vs 422 구분:**
- `409`: 현재 **리소스 상태**와 요청이 충돌하는 경우 (상태 의존적)
- `422`: 리소스 상태와 무관하게 입력값 자체가 유효하지 않은 경우

---

## 응답 형식

### 성공 응답 — 단일 리소스

```json
{
  "data": {
    "id": "uuid",
    "name": "My Space",
    "created_at": "2026-06-02T09:00:00Z"
  }
}
```

### 성공 응답 — 목록

```json
{
  "data": [
    { "id": "uuid", "name": "My Space" }
  ],
  "meta": {
    "cursor": "eyJpZCI6InV1aWQifQ==",
    "has_more": true,
    "limit": 20
  }
}
```

cursor는 불투명(opaque) Base64 문자열. 클라이언트는 내부 구조 파싱 금지.

### 성공 응답 — 202 Accepted (비동기)

```json
{
  "data": {
    "job_id": "uuid",
    "status": "queued",
    "status_url": "/api/v1/pipeline/jobs/uuid",
    "estimated_seconds": 30
  }
}
```

### 에러 응답

RFC 7807 필드명 차용. `type` URI는 Phase 2 공개 API 전환 시 추가.

```json
{
  "status": 404,
  "code": "SPACE_NOT_FOUND",
  "message": "Space를 찾을 수 없습니다",
  "detail": "space_id 'abc-123'에 해당하는 Space가 없습니다",
  "instance": "/api/v1/spaces/abc-123",
  "trace_id": "req-7f3a9abc"
}
```

| 필드 | 설명 |
|------|------|
| `status` | HTTP 상태 코드 (body 자체로 완결되도록 중복 포함) |
| `code` | 클라이언트 분기 처리용 에러 코드 (도메인\_엔티티\_오류유형) |
| `message` | 사람이 읽을 수 있는 짧은 설명 |
| `detail` | 디버깅용 상세 설명 (프로덕션 환경에서도 포함) |
| `instance` | 에러가 발생한 요청 경로 |
| `trace_id` | `X-Request-ID`와 동일값. 서버 로그 연계용 |

### 422 — 입력 검증 에러 (다중 필드)

```json
{
  "status": 422,
  "code": "VALIDATION_ERROR",
  "message": "입력값이 유효하지 않습니다",
  "detail": "요청 본문에 유효하지 않은 필드가 있습니다",
  "instance": "/api/v1/groups",
  "trace_id": "req-7f3a9abc",
  "errors": [
    { "field": "name", "code": "REQUIRED", "message": "필수 항목입니다" },
    { "field": "role", "code": "INVALID_ENUM", "message": "'superuser'는 허용되지 않습니다. 허용값: owner, admin, member, viewer" }
  ]
}
```

---

## 도메인 에러 코드 체계

네이밍 규칙: `{도메인}_{에러유형}`

### AUTH

| code | HTTP | 설명 |
|------|------|------|
| `AUTH_TOKEN_MISSING` | 401 | Authorization 헤더 없음 |
| `AUTH_TOKEN_EXPIRED` | 401 | JWT 만료 |
| `AUTH_TOKEN_INVALID` | 401 | JWT 서명 검증 실패 |
| `AUTH_USER_NOT_FOUND` | 404 | users 테이블에 없는 사용자 |
| `AUTH_USER_DELETED` | 403 | soft delete된 계정 |

### SPACE

| code | HTTP | 설명 |
|------|------|------|
| `SPACE_NOT_FOUND` | 404 | Space 없음 |
| `SPACE_ACCESS_DENIED` | 403 | Space 접근 권한 없음 |
| `SPACE_UPDATE_FORBIDDEN` | 403 | 수정 권한 없음 (viewer가 수정 시도 등) |

### GROUP

| code | HTTP | 설명 |
|------|------|------|
| `GROUP_NOT_FOUND` | 404 | Group 없음 |
| `GROUP_ACCESS_DENIED` | 403 | Group 접근 권한 없음 |
| `GROUP_MEMBER_ALREADY_EXISTS` | 409 | 이미 멤버인 사용자 초대 시도 |
| `GROUP_MEMBER_NOT_FOUND` | 404 | 멤버가 아닌 사용자 조작 시도 |
| `GROUP_ROLE_INSUFFICIENT` | 403 | 역할 권한 부족 (member가 admin 작업 시도) |
| `GROUP_OWNER_CANNOT_LEAVE` | 409 | owner는 직접 탈퇴 불가 (역할 양도 필요) |

### NODE (GraphQL에서 사용 — `errors` 배열에 포함)

| code | 설명 |
|------|------|
| `NODE_NOT_FOUND` | Node 없음 |
| `NODE_STATUS_CONFLICT` | 이미 confirmed/rejected 상태인 노드를 다시 상태 변경 시도 |
| `NODE_LABEL_DUPLICATE` | (space_id, node_type, label) unique 위반 |
| `NODE_ACCESS_DENIED` | 해당 Space의 Node 접근 권한 없음 |

### PIPELINE

| code | HTTP | 설명 |
|------|------|------|
| `PIPELINE_JOB_NOT_FOUND` | 404 | Job ID 없음 |
| `PIPELINE_JOB_NOT_COMPLETE` | 409 | 완료되지 않은 Job 결과 조회 시도 |
| `PIPELINE_SOURCE_TYPE_UNSUPPORTED` | 422 | 허용되지 않는 source type |
| `PIPELINE_URL_UNREACHABLE` | 422 | URL 크롤링 불가 (접근 차단, 404 등) |
| `PIPELINE_FILE_TOO_LARGE` | 422 | 파일 크기 초과 (PDF 최대 50MB) |
| `PIPELINE_YOUTUBE_CAPTION_UNAVAILABLE` | 422 | 자막 없는 YouTube 영상 |

### 공통

| code | HTTP | 설명 |
|------|------|------|
| `VALIDATION_ERROR` | 422 | 입력값 검증 실패 (다중 필드 시 `errors` 배열 포함) |
| `RATE_LIMIT_EXCEEDED` | 429 | 요청 과다 |
| `INTERNAL_ERROR` | 500 | 서버 내부 오류 |
| `UPSTREAM_ERROR` | 502 | 외부 서비스 오류 (LLM API, Supabase) |
| `SERVICE_UNAVAILABLE` | 503 | 서비스 점검 중 |

---

## 날짜/시간 형식

모든 날짜는 **ISO 8601 + UTC**.

```json
"created_at": "2026-06-02T09:00:00Z"
```

- Unix Timestamp만 쓰지 않음 (디버깅 불편)
- 클라이언트에서 로컬 타임존 변환 처리

---

## API 버저닝 전략

### 현재: URL 버저닝

```
/api/v1/...
```

### Breaking Change 기준 (v2 생성 조건)

아래 중 하나라도 해당하면 v2 생성:
- 응답 필드 제거 또는 타입 변경
- 필수 요청 필드 추가
- 엔드포인트 URL 변경 또는 삭제
- 인증 방식 변경
- 동작 방식 변경 (같은 입력에 다른 결과)

### Non-Breaking Change (v1 유지 가능)

- 응답에 새 필드 추가
- 선택 요청 필드 추가
- 새 엔드포인트 추가
- 성능 개선

### Deprecated 처리

v2 출시 시 v1에 deprecation 헤더 추가. 최소 6개월 병행 운영.

```
Deprecation: true
Sunset: Mon, 02 Jun 2027 00:00:00 GMT
Link: </api/v2/spaces>; rel="successor-version"
```

---

## Rate Limiting

| 대상 | 제한 |
|------|------|
| 일반 API | 100 req/min per user |
| POST /api/v1/sources | 10 req/min per user (AI 처리 비용) |
| POST /graphql | 60 req/min per user |

**응답 헤더 (모든 요청):**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1748876400
```

**429 응답 헤더:**
```
Retry-After: 60
```

---

## 페이지네이션

Cursor 기반 (모바일 무한 스크롤 친화).

```
GET /api/v1/spaces?limit=20&after=<cursor>
GET /api/v1/spaces?limit=20&before=<cursor>
```

| 파라미터 | 기본값 | 최대값 |
|---------|--------|--------|
| `limit` | 20 | 50 |
| `after` | — | cursor 문자열 |
| `before` | — | cursor 문자열 |

---

## Auth 모듈 (REST)

### 개요

Supabase Auth가 실제 인증(로그인/회원가입/토큰 갱신)을 담당.  
FastAPI Auth 모듈은 프로필 관리와 Supabase webhook 수신만 처리.

> 로그인/회원가입은 클라이언트가 Supabase SDK 직접 호출.  
> FastAPI는 발급된 JWT를 검증하는 역할만 한다.

---

### GET /api/v1/auth/me

내 프로필 조회.

**Response 200**
```json
{
  "data": {
    "id": "uuid",
    "display_name": "Laze",
    "personal_space_id": "uuid",
    "default_strategy_id": "uuid | null",
    "created_at": "2026-06-02T09:00:00Z"
  }
}
```

**에러 케이스**

| 상황 | code | HTTP |
|------|------|------|
| JWT 없음/만료 | `AUTH_TOKEN_MISSING` / `AUTH_TOKEN_EXPIRED` | 401 |
| users 테이블에 없음 (webhook 미처리) | `AUTH_USER_NOT_FOUND` | 404 |

---

### PATCH /api/v1/auth/me

프로필 수정.

**Request**
```json
{
  "display_name": "New Name",
  "default_strategy_id": "uuid | null"
}
```

**Response 200** — 수정된 프로필 (GET /me 동일 구조)

**에러 케이스**

| 상황 | code | HTTP |
|------|------|------|
| `display_name` 빈 문자열 | `VALIDATION_ERROR` | 422 |

---

### DELETE /api/v1/auth/me

계정 비활성화 (soft delete).

**Response 204** No Content

---

### POST /api/v1/auth/webhook

Supabase Auth 이벤트 수신. 회원가입 시 `users` 테이블 + 개인 Space 자동 생성.

**Headers**
```
X-Supabase-Webhook-Secret: <server_secret>
```

**Request (Supabase 전송)**
```json
{
  "type": "INSERT",
  "table": "auth.users",
  "record": {
    "id": "uuid",
    "email": "user@example.com"
  }
}
```

**Response 200** OK

**에러 케이스**

| 상황 | code | HTTP |
|------|------|------|
| 시크릿 불일치 | `AUTH_TOKEN_INVALID` | 401 |

---

## Space 모듈 (REST)

### 개요

Space = 순수 지식 컨테이너. 개인 Space는 회원가입 시 자동 생성 (직접 생성 불가).  
그룹 Space는 그룹 생성 시 자동 생성.

---

### GET /api/v1/spaces

내가 접근 가능한 Space 목록 (개인 + 소속 그룹).

**Query Parameters**

| 파라미터 | 타입 | 기본값 |
|---------|------|--------|
| `limit` | int | 20 |
| `after` | string | — |

**Response 200**
```json
{
  "data": [
    {
      "id": "uuid",
      "name": "My Space",
      "owner_type": "personal",
      "is_public": false,
      "created_at": "2026-06-02T09:00:00Z"
    }
  ],
  "meta": {
    "cursor": "eyJpZCI6InV1aWQifQ==",
    "has_more": false,
    "limit": 20
  }
}
```

---

### GET /api/v1/spaces/:space_id

Space 상세 조회.

**Response 200**
```json
{
  "data": {
    "id": "uuid",
    "name": "My Space",
    "owner_type": "personal",
    "is_public": false,
    "default_strategy_id": "uuid | null",
    "created_at": "2026-06-02T09:00:00Z"
  }
}
```

**에러 케이스**

| 상황 | code | HTTP |
|------|------|------|
| Space 없음 | `SPACE_NOT_FOUND` | 404 |
| 비공개 Space에 비멤버 접근 | `SPACE_ACCESS_DENIED` | 403 |

---

### PATCH /api/v1/spaces/:space_id

Space 설정 수정. 개인 Space: 본인만. 그룹 Space: owner/admin만.

**Request**
```json
{
  "name": "Updated Name",
  "is_public": true,
  "default_strategy_id": "uuid | null"
}
```

**Response 200** — 수정된 Space (GET 상세 동일 구조)

**에러 케이스**

| 상황 | code | HTTP |
|------|------|------|
| Space 없음 | `SPACE_NOT_FOUND` | 404 |
| 수정 권한 없음 | `SPACE_UPDATE_FORBIDDEN` | 403 |

---

### POST /api/v1/groups

그룹 생성. 그룹 Space 자동 생성 + 생성자 owner 등록.

**Request**
```json
{
  "name": "AI Study Group",
  "is_public": false,
  "require_approval": false
}
```

**Response 201**

```
Location: /api/v1/groups/uuid
```

```json
{
  "data": {
    "id": "uuid",
    "name": "AI Study Group",
    "space_id": "uuid",
    "is_public": false,
    "require_approval": false,
    "auto_approve_roles": ["owner", "admin"],
    "created_at": "2026-06-02T09:00:00Z"
  }
}
```

**에러 케이스**

| 상황 | code | HTTP |
|------|------|------|
| `name` 누락 | `VALIDATION_ERROR` | 422 |

---

### GET /api/v1/groups/:group_id

그룹 상세. 소속 멤버만 조회 가능 (public 그룹은 누구나).

**Response 200** — 그룹 정보 (POST 응답 동일 구조)

**에러 케이스**

| 상황 | code | HTTP |
|------|------|------|
| 그룹 없음 | `GROUP_NOT_FOUND` | 404 |
| 비공개 그룹에 비멤버 접근 | `GROUP_ACCESS_DENIED` | 403 |

---

### PATCH /api/v1/groups/:group_id

그룹 설정 수정. owner/admin만.

**Request**
```json
{
  "name": "New Name",
  "is_public": true,
  "require_approval": true,
  "auto_approve_roles": ["owner", "admin", "member"]
}
```

**Response 200** — 수정된 그룹

**에러 케이스**

| 상황 | code | HTTP |
|------|------|------|
| 그룹 없음 | `GROUP_NOT_FOUND` | 404 |
| 권한 없음 (member/viewer가 수정 시도) | `GROUP_ROLE_INSUFFICIENT` | 403 |

---

### DELETE /api/v1/groups/:group_id

그룹 해산 (soft delete). owner만.

**Response 204** No Content

**에러 케이스**

| 상황 | code | HTTP |
|------|------|------|
| 그룹 없음 | `GROUP_NOT_FOUND` | 404 |
| owner 외 시도 | `GROUP_ROLE_INSUFFICIENT` | 403 |

---

### GET /api/v1/groups/:group_id/members

멤버 목록.

**Response 200**
```json
{
  "data": [
    {
      "user_id": "uuid",
      "display_name": "Alice",
      "role": "owner",
      "joined_at": "2026-06-02T09:00:00Z"
    }
  ],
  "meta": {
    "cursor": null,
    "has_more": false,
    "limit": 20
  }
}
```

---

### POST /api/v1/groups/:group_id/members

멤버 초대. owner/admin만.

**Request**
```json
{
  "user_id": "uuid",
  "role": "member"
}
```

**Response 201**

```
Location: /api/v1/groups/uuid/members/user-uuid
```

```json
{
  "data": {
    "user_id": "uuid",
    "display_name": "Bob",
    "role": "member",
    "joined_at": "2026-06-02T09:00:00Z"
  }
}
```

**에러 케이스**

| 상황 | code | HTTP |
|------|------|------|
| 이미 멤버인 사용자 | `GROUP_MEMBER_ALREADY_EXISTS` | 409 |
| 초대자 권한 없음 | `GROUP_ROLE_INSUFFICIENT` | 403 |
| 유효하지 않은 `role` 값 | `VALIDATION_ERROR` | 422 |

---

### PATCH /api/v1/groups/:group_id/members/:user_id

역할 변경. owner만.

**Request**
```json
{
  "role": "admin"
}
```

**Response 200** — 수정된 멤버 정보

**에러 케이스**

| 상황 | code | HTTP |
|------|------|------|
| 멤버 없음 | `GROUP_MEMBER_NOT_FOUND` | 404 |
| owner 외 시도 | `GROUP_ROLE_INSUFFICIENT` | 403 |

---

### DELETE /api/v1/groups/:group_id/members/:user_id

멤버 제거 / 탈퇴 (자기 자신도 가능). owner는 직접 탈퇴 불가.

**Response 204** No Content

**에러 케이스**

| 상황 | code | HTTP |
|------|------|------|
| 멤버 없음 | `GROUP_MEMBER_NOT_FOUND` | 404 |
| owner가 자신을 제거 시도 | `GROUP_OWNER_CANNOT_LEAVE` | 409 |
| 다른 멤버 제거 권한 없음 | `GROUP_ROLE_INSUFFICIENT` | 403 |

---

## Knowledge 모듈 (GraphQL)

### 개요

`POST /graphql` 단일 엔드포인트. 모든 요청에 JWT 필수.  
GraphQL 에러는 HTTP 200 + `errors` 배열로 반환 (GraphQL 표준).

```json
{
  "data": null,
  "errors": [
    {
      "message": "Space를 찾을 수 없습니다",
      "extensions": {
        "code": "SPACE_NOT_FOUND",
        "status": 404,
        "trace_id": "req-7f3a9abc"
      }
    }
  ]
}
```

---

### Schema

```graphql
# ── 타입 정의 ──────────────────────────────────────────

enum NodeType { P C M D }
enum NodeStatus { draft confirmed rejected }
enum RelationType {
  DECOMPOSE_TO
  MANIFESTS_AS
  INSTANTIATED_BY
  CONNECTS_TO
  ANALOGOUS_TO
  BELONGS_TO
}

type Node {
  id: ID!
  spaceId: ID!
  nodeType: NodeType!
  label: String!
  displayName: String!
  description: String
  status: NodeStatus!
  createdBy: ID!
  createdAt: String!

  # 연결 필드 (요청 시에만 resolve)
  relationships: [Relationship!]
  sources: [Source!]
}

type Relationship {
  id: ID!
  spaceId: ID!
  fromNode: Node!
  toNode: Node!
  relationType: RelationType!
  createdBy: ID!
  createdAt: String!
}

type Source {
  id: ID!
  type: String!
  metadata: JSON
  createdAt: String!
}

type Graph {
  nodes: [Node!]!
  relationships: [Relationship!]!
}

type NodeConnection {
  edges: [NodeEdge!]!
  pageInfo: PageInfo!
}

type NodeEdge {
  cursor: String!
  node: Node!
}

type PageInfo {
  hasNextPage: Boolean!
  endCursor: String
}

scalar JSON

# ── 입력 타입 ──────────────────────────────────────────

input NodeFilter {
  nodeType: NodeType
  status: NodeStatus
  query: String        # label 또는 displayName 부분 검색
}

input NodeUpdateInput {
  displayName: String
  description: String
  nodeType: NodeType
}

input RelationshipInput {
  spaceId: ID!
  fromNodeId: ID!
  toNodeId: ID!
  relationType: RelationType!
}

# ── Query ──────────────────────────────────────────────

type Query {
  # 단일 노드
  node(id: ID!): Node

  # 노드 목록 (cursor 페이지네이션)
  nodes(
    spaceId: ID!
    filter: NodeFilter
    first: Int = 20
    after: String
  ): NodeConnection!

  # 그래프 전체 (노드 + 관계)
  graph(
    spaceId: ID!
    depth: Int = 2
    filter: NodeFilter
  ): Graph!

  # 노드 + 연결된 소스
  nodeWithSources(id: ID!): Node
}

# ── Mutation ───────────────────────────────────────────

type Mutation {
  # 노드 상태 변경 (draft → confirmed/rejected)
  confirmNode(id: ID!): Node!
  rejectNode(id: ID!): Node!

  # 노드 편집
  updateNode(id: ID!, input: NodeUpdateInput!): Node!

  # 노드 soft delete
  deleteNode(id: ID!): Boolean!

  # 관계 생성 / 삭제
  createRelationship(input: RelationshipInput!): Relationship!
  deleteRelationship(id: ID!): Boolean!
}
```

### 에러 케이스 (주요 Operation별)

| Operation | 에러 상황 | code |
|-----------|----------|------|
| `graph`, `nodes` | Space 없음 | `SPACE_NOT_FOUND` |
| `graph`, `nodes` | Space 접근 권한 없음 | `SPACE_ACCESS_DENIED` |
| `node` | Node 없음 | `NODE_NOT_FOUND` |
| `confirmNode`, `rejectNode` | 이미 confirmed/rejected | `NODE_STATUS_CONFLICT` |
| `updateNode` | label 중복 | `NODE_LABEL_DUPLICATE` |
| `createRelationship` | fromNode 또는 toNode 없음 | `NODE_NOT_FOUND` |

### 쿼리 예시

**그래프 조회**
```graphql
query GetGraph($spaceId: ID!) {
  graph(spaceId: $spaceId, depth: 2) {
    nodes {
      id
      nodeType
      label
      displayName
      status
    }
    relationships {
      id
      fromNode { id }
      toNode { id }
      relationType
    }
  }
}
```

**draft 노드 목록 + 소스**
```graphql
query GetDraftNodes($spaceId: ID!) {
  nodes(spaceId: $spaceId, filter: { status: draft }, first: 20) {
    edges {
      node {
        id
        displayName
        nodeType
        sources { id type metadata }
      }
    }
    pageInfo { hasNextPage endCursor }
  }
}
```

**노드 확정**
```graphql
mutation ConfirmNode($id: ID!) {
  confirmNode(id: $id) {
    id
    status
  }
}
```

---

## AI Pipeline 모듈 (REST + Polling + SSE)

### 개요

비동기 처리 흐름:
```
POST /api/v1/sources
  → HTTP 202 + job_id + status_url 즉시 반환
  → Background Task 실행 (크롤링/파싱 → 청킹 → LLM 추출 → 임베딩)

GET /api/v1/pipeline/jobs/:job_id          ← 상태 폴링 (기본)
GET /api/v1/pipeline/jobs/:job_id/stream   ← SSE 스트림 (LLM 추출 텍스트 실시간)
GET /api/v1/pipeline/jobs/:job_id/result   ← 완료 후 노드 목록
```

**Web vs Mobile 처리 방식**

| | Web | Mobile (Expo) |
|---|---|---|
| 폴링 | fetch + setTimeout | fetch + setTimeout (동일) |
| SSE | native EventSource | react-native-sse 폴리필 |
| 파일 업로드 | `<input type="file">` → FormData | expo-document-picker → FormData |

**Job 상태 흐름**

```
queued → processing → succeeded
                    ↘ failed
```

**폴링 권장 간격** (exponential backoff)

```
1s → 2s → 4s → 8s → 10s (max, 이후 고정)
```

---

### POST /api/v1/sources

소스 업로드 및 처리 Job 생성.

**Request (URL)**
```json
{
  "space_id": "uuid",
  "type": "url",
  "url": "https://example.com/article"
}
```

**Request (PDF)** — `multipart/form-data`
```
space_id: uuid
type: pdf
file: <binary>       최대 50MB
```

**Request (텍스트)**
```json
{
  "space_id": "uuid",
  "type": "text",
  "content": "직접 입력한 텍스트 내용"
}
```

**Request (YouTube)**
```json
{
  "space_id": "uuid",
  "type": "youtube",
  "url": "https://youtube.com/watch?v=xxx"
}
```

**Response 202**

```
Location: /api/v1/pipeline/jobs/uuid
```

```json
{
  "data": {
    "job_id": "uuid",
    "source_id": "uuid",
    "status": "queued",
    "status_url": "/api/v1/pipeline/jobs/uuid",
    "estimated_seconds": 30,
    "created_at": "2026-06-02T09:00:00Z"
  }
}
```

**에러 케이스**

| 상황 | code | HTTP |
|------|------|------|
| Space 없음 | `SPACE_NOT_FOUND` | 404 |
| Space 접근 권한 없음 | `SPACE_ACCESS_DENIED` | 403 |
| 허용되지 않는 type | `PIPELINE_SOURCE_TYPE_UNSUPPORTED` | 422 |
| PDF 크기 초과 | `PIPELINE_FILE_TOO_LARGE` | 422 |
| `space_id` 누락 | `VALIDATION_ERROR` | 422 |

---

### GET /api/v1/pipeline/jobs/:job_id

Job 상태 폴링.

**Response 200 — queued / processing**
```json
{
  "data": {
    "job_id": "uuid",
    "status": "processing",
    "stage": "chunking",
    "progress": {
      "stages_done": 1,
      "stages_total": 4,
      "stage_labels": ["crawling", "chunking", "extracting", "embedding"]
    },
    "created_at": "2026-06-02T09:00:00Z",
    "updated_at": "2026-06-02T09:00:05Z"
  }
}
```

**Response 200 — succeeded**
```json
{
  "data": {
    "job_id": "uuid",
    "status": "succeeded",
    "result": {
      "source_id": "uuid",
      "nodes_extracted": 12,
      "space_id": "uuid",
      "result_url": "/api/v1/pipeline/jobs/uuid/result"
    },
    "created_at": "2026-06-02T09:00:00Z",
    "completed_at": "2026-06-02T09:00:30Z"
  }
}
```

**Response 200 — failed**
```json
{
  "data": {
    "job_id": "uuid",
    "status": "failed",
    "error": {
      "code": "PIPELINE_URL_UNREACHABLE",
      "message": "URL에 접근할 수 없습니다"
    },
    "created_at": "2026-06-02T09:00:00Z",
    "completed_at": "2026-06-02T09:00:10Z"
  }
}
```

**에러 케이스**

| 상황 | code | HTTP |
|------|------|------|
| Job 없음 | `PIPELINE_JOB_NOT_FOUND` | 404 |

---

### GET /api/v1/pipeline/jobs/:job_id/stream

LLM 노드 추출 단계 SSE 스트림.

**Response Headers**
```
Content-Type: text/event-stream
Cache-Control: no-cache
X-Accel-Buffering: no
```

**SSE 이벤트 흐름**

```
event: job_started
data: {"job_id":"uuid","stage":"extracting"}

event: node_delta
data: {"node_type":"C","display_name":"강화학습","partial":true}

event: node_complete
data: {"node_type":"C","display_name":"강화학습","label":"reinforcement-learning","description":"에이전트가 환경과 상호작용하며 보상을 최대화하는 학습 방식"}

event: job_done
data: {"job_id":"uuid","nodes_extracted":12,"status":"succeeded"}

event: job_error
data: {"code":"UPSTREAM_ERROR","message":"LLM API 오류가 발생했습니다"}
```

**클라이언트 fallback 전략**
```
1. SSE 연결 시도 (3초 타임아웃)
2. 연결 실패 → 폴링 모드로 전환
   exponential backoff: 1s → 2s → 4s → 8s → 10s (max)
3. job_error 이벤트 수신 → 폴링으로 최종 상태 확인
```

---

### GET /api/v1/pipeline/jobs/:job_id/result

Job 완료 후 추출된 노드 목록. `status: succeeded` 이후에만 유효.

**Response 200**
```json
{
  "data": {
    "job_id": "uuid",
    "source_id": "uuid",
    "nodes": [
      {
        "id": "uuid",
        "node_type": "C",
        "label": "reinforcement-learning",
        "display_name": "강화학습",
        "description": "에이전트가 환경과 상호작용하며 보상을 최대화하는 학습 방식",
        "status": "draft"
      }
    ]
  }
}
```

> 이후 노드 확정/거부는 GraphQL `confirmNode` / `rejectNode` Mutation 사용.

**에러 케이스**

| 상황 | code | HTTP |
|------|------|------|
| Job 없음 | `PIPELINE_JOB_NOT_FOUND` | 404 |
| 아직 완료 안 됨 | `PIPELINE_JOB_NOT_COMPLETE` | 409 |

---

## 내부 gRPC 계약

Phase 1은 Modular Monolith — 아래 인터페이스를 Python 함수로 구현.  
MSA 전환 시 동일 `.proto`로 gRPC 서버/클라이언트 생성.

```protobuf
syntax = "proto3";
package epistruct.internal.v1;

// ── Auth Service ──────────────────────────────────────

service AuthService {
  rpc ValidateUser (ValidateUserRequest) returns (ValidateUserResponse);
  rpc GetUser (GetUserRequest) returns (GetUserResponse);
}

message ValidateUserRequest { string jwt = 1; }
message ValidateUserResponse {
  string user_id = 1;
  string personal_space_id = 2;
  bool valid = 3;
  string error_code = 4;   // AUTH_TOKEN_EXPIRED 등
}
message GetUserRequest { string user_id = 1; }
message GetUserResponse {
  string user_id = 1;
  string display_name = 2;
  string personal_space_id = 3;
}

// ── Space Service ─────────────────────────────────────

service SpaceService {
  rpc CheckSpaceAccess (CheckSpaceAccessRequest) returns (CheckSpaceAccessResponse);
  rpc GetSpace (GetSpaceRequest) returns (GetSpaceResponse);
}

message CheckSpaceAccessRequest {
  string user_id = 1;
  string space_id = 2;
  string required_role = 3;  // "viewer" | "member" | "admin" | "owner"
}
message CheckSpaceAccessResponse {
  bool allowed = 1;
  string role = 2;
  string error_code = 3;  // SPACE_NOT_FOUND | SPACE_ACCESS_DENIED
}
message GetSpaceRequest { string space_id = 1; }
message GetSpaceResponse {
  string space_id = 1;
  string owner_type = 2;
  bool is_public = 3;
}

// ── Knowledge Service ─────────────────────────────────

service KnowledgeService {
  rpc CreateNodes (CreateNodesRequest) returns (CreateNodesResponse);
}

message NodeProto {
  string node_type = 1;
  string label = 2;
  string display_name = 3;
  string description = 4;
  string created_by = 5;
}
message CreateNodesRequest {
  string space_id = 1;
  string source_id = 2;
  string job_id = 3;
  repeated NodeProto nodes = 4;
}
message CreateNodesResponse {
  repeated string node_ids = 1;
  int32 created_count = 2;
  repeated string skipped_labels = 3;  // NODE_LABEL_DUPLICATE로 건너뛴 label 목록
}

// ── Pipeline Service ──────────────────────────────────

service PipelineService {
  rpc EnqueueSource (EnqueueSourceRequest) returns (EnqueueSourceResponse);
  rpc GetJobStatus (GetJobStatusRequest) returns (GetJobStatusResponse);
}

message EnqueueSourceRequest {
  string space_id = 1;
  string source_id = 2;
  string created_by = 3;
}
message EnqueueSourceResponse { string job_id = 1; }
message GetJobStatusRequest { string job_id = 1; }
message GetJobStatusResponse {
  string job_id = 1;
  string status = 2;
  string stage = 3;
  string error_code = 4;
}
```

---

## 모듈 간 호출 흐름

### 소스 업로드 전체 흐름

```
클라이언트
  → POST /api/v1/sources
       │
       ├─ AuthService.ValidateUser(jwt)
       ├─ SpaceService.CheckSpaceAccess(user_id, space_id, "member")
       ├─ sources 테이블 저장
       ├─ PipelineService.EnqueueSource(space_id, source_id, user_id)
       └─ HTTP 202 + { job_id, status_url, estimated_seconds }

Background Task
  → 크롤링/파싱 → 청킹 → LLM 추출
  → KnowledgeService.CreateNodes(space_id, source_id, job_id, nodes)
  → 임베딩 생성 (BackgroundTask)
  → job status = succeeded
```

### 그래프 조회 흐름

```
클라이언트
  → POST /graphql { query: graph(spaceId: ...) }
       │
       ├─ AuthService.ValidateUser(jwt)
       ├─ SpaceService.CheckSpaceAccess(user_id, space_id, "viewer")
       └─ nodes + node_relationships 조회 반환
```

---

## 미결 사항 (Phase 1-B 착수 전)

| 항목 | 내용 |
|------|------|
| `learning_strategies` API | Strategy CRUD + 기본값 설정 엔드포인트 미정 |
| `node_proposals` API | 그룹 승인 플로우 상세 UX 확정 후 설계 |
| GraphQL Subscription | 실시간 노드 확정 알림 필요 시 추가 검토 |
| `type` URI 관리 | Phase 2 공개 API 전환 시 RFC 7807 `type` 필드 추가 |
