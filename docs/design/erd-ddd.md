# Epistruct — 도메인 모델 & ERD (DDD 기반)

> 작성일: 2026-06-02
> 적용 원칙: DDD Bounded Context + Aggregate 분리

---

## 도메인 맵

```
┌──────────────────────────────────────────────────────┐
│  User Domain          │  Strategy Domain             │
│  users                │  learning_strategies         │
│                       │  (user/group/system 소유)    │
├───────────────────────┼──────────────────────────────┤
│  Space Domain         │  Group Domain                │
│  spaces               │  groups                      │
│  ├─ nodes             │  └─ group_members            │
│  ├─ node_relationships│                              │
│  ├─ sources           │  groups.space_id → spaces    │
│  ├─ chunks            │  (그룹의 지식은 Space에 있음)│
│  └─ node_sources      │                              │
└───────────────────────┴──────────────────────────────┘
```

---

## 설계 원칙

| 원칙 | 내용 |
|------|------|
| Space는 순수 지식 컨테이너 | 소유자 정보 없음. 노드·소스를 담는 그릇. `owner_type`으로 분기 힌트만 보유 |
| 소유 방향은 소유자 → Space | `users.personal_space_id`, `groups.space_id` 모두 소유자 쪽에서 Space를 참조 |
| 멤버십은 Group 도메인 | 개인 공간에는 멤버십 개념 없음. `group_members`만 존재 |
| 소유권 유일성 | `users.personal_space_id UNIQUE`, `groups.space_id UNIQUE` — 한 Space는 정확히 하나의 소유자 |
| DB FK 없음 | UUID 참조만 보유. 참조 무결성은 application 레벨 보장 |
| Soft delete 필수 | 모든 주요 테이블 `deleted_at TIMESTAMPTZ` — 물리 DELETE 없음 |

---

## 테이블 정의

### User Domain

```sql
users
  id                   UUID        PK
  personal_space_id    UUID        UNIQUE  -- → spaces.id (회원가입 시 생성)
  display_name         VARCHAR
  default_strategy_id  UUID        NULL    -- → learning_strategies
  created_at           TIMESTAMPTZ
  deleted_at           TIMESTAMPTZ
```

---

### Space Domain (순수 지식 컨테이너)

```sql
spaces
  id                   UUID        PK
  owner_type           ENUM('personal','group')  -- 역조회 분기 힌트 (반정규화)
  name                 VARCHAR
  is_public            BOOLEAN     DEFAULT false
  default_strategy_id  UUID        NULL  -- → learning_strategies
  created_at           TIMESTAMPTZ
  deleted_at           TIMESTAMPTZ
```

> 소유자 ID는 spaces가 보유하지 않음. 소유 관계는 `users.personal_space_id`, `groups.space_id`에서 단방향 참조.
> `owner_type`은 "이 space는 개인/그룹 중 어디서 찾아야 하나"를 알려주는 힌트 컬럼. 중복 저장이지만 역조회 시 조건 분기를 단순화.

```sql
nodes
  id            UUID        PK
  space_id      UUID        -- → spaces.id
  created_by    UUID        -- → users.id
  node_type     ENUM('P','C','M','D')
  label         VARCHAR     -- 입력 그대로 보존. (space_id, node_type, label) unique (대소문자 무시)
  description   TEXT
  status        ENUM('draft','confirmed','rejected')
  embedding     vector(1536)
  created_at    TIMESTAMPTZ
  deleted_at    TIMESTAMPTZ

  UNIQUE (space_id, node_type, label)
```

```sql
node_relationships
  id            UUID        PK
  space_id      UUID        -- → spaces.id
  from_node_id  UUID        -- → nodes.id
  to_node_id    UUID        -- → nodes.id
  relation_type ENUM('DECOMPOSE_TO','MANIFESTS_AS','INSTANTIATED_BY',
                     'CONNECTS_TO','ANALOGOUS_TO','BELONGS_TO')
  created_by    UUID        -- → users.id
  created_at    TIMESTAMPTZ
```

```sql
sources
  id           UUID        PK
  space_id     UUID        -- → spaces.id
  created_by   UUID        -- → users.id
  type         ENUM('url','pdf','youtube','text','conversation')
  raw_content  TEXT
  metadata     JSONB
  created_at   TIMESTAMPTZ
  deleted_at   TIMESTAMPTZ
```

```sql
chunks
  id          UUID        PK
  source_id   UUID        -- → sources.id
  content     TEXT
  embedding   vector(1536)
  chunk_index INTEGER
  created_at  TIMESTAMPTZ
```

```sql
node_sources  -- Node ↔ Source N:M 브릿지
  node_id    UUID  -- → nodes.id
  source_id  UUID  -- → sources.id
  PK: (node_id, source_id)
```

```sql
node_lineage  -- 공간 간 이동 계보 (Phase 2)
  id              UUID        PK
  origin_node_id  UUID        -- → nodes.id (원본)
  derived_node_id UUID        -- → nodes.id (재구성 결과)
  moved_by        UUID        -- → users.id
  moved_at        TIMESTAMPTZ
```

---

### Group Domain

```sql
groups
  id                        UUID        PK
  space_id                  UUID        UNIQUE  -- 그룹이 소유한 지식 공간 → spaces.id
  name                      VARCHAR
  is_public                 BOOLEAN     DEFAULT false
  require_approval          BOOLEAN     DEFAULT false
  auto_approve_roles        TEXT[]      DEFAULT '{owner,admin}'
  strategy_override_allowed BOOLEAN     DEFAULT true
  default_strategy_id       UUID        NULL  -- → learning_strategies
  created_at                TIMESTAMPTZ
  deleted_at                TIMESTAMPTZ
```

```sql
group_members
  group_id   UUID
  user_id    UUID
  role       ENUM('owner','admin','member','viewer')
  joined_at  TIMESTAMPTZ
  PK: (group_id, user_id)
```

```sql
node_proposals  -- 그룹 노드 변경 제안 (require_approval=true 시, Phase 2)
  id           UUID        PK
  space_id     UUID        -- → spaces.id
  proposed_by  UUID        -- → users.id
  node_id      UUID        NULL  -- NULL: 새 노드 생성 제안
  action       ENUM('create','update','delete')
  payload      JSONB
  status       ENUM('pending','approved','rejected')
  reviewed_by  UUID        NULL
  reviewed_at  TIMESTAMPTZ NULL
  created_at   TIMESTAMPTZ
```

---

### Strategy Domain

```sql
learning_strategies
  id          UUID        PK
  user_id     UUID        NULL  -- 사용자 소유 전략
  group_id    UUID        NULL  -- 그룹 소유 전략
  is_system   BOOLEAN     DEFAULT false  -- user_id, group_id 모두 NULL이면 시스템 템플릿
  name        VARCHAR
  description TEXT
  config      JSONB       -- 스타일 파라미터 (소크라테스식, 사례형 등)
  created_at  TIMESTAMPTZ
  deleted_at  TIMESTAMPTZ

  -- 제약: user_id, group_id, is_system 중 정확히 하나만 활성 (application 레벨)
```

---

## 도메인 간 연결 요약

```
users ── personal_space_id ──→ spaces
  │                               │
  │ default_strategy_id           └── nodes, sources, chunks, node_sources
  │
  └→ learning_strategies ←── groups (default_strategy_id)

groups ── space_id ──→ spaces
  └── group_members (user_id → users)
```

소유 방향: 소유자(users/groups) → Space. spaces는 소유자를 모름.

---

## "내가 접근할 수 있는 모든 공간" 조회

소유 관계가 users/groups에 있으므로 두 경로를 UNION:

```sql
-- 개인 공간
SELECT s.id FROM spaces s
JOIN users u ON u.personal_space_id = s.id
WHERE u.id = $1 AND s.deleted_at IS NULL

UNION

-- 그룹 공간
SELECT s.id FROM spaces s
JOIN groups g ON g.space_id = s.id
JOIN group_members gm ON gm.group_id = g.id
WHERE gm.user_id = $1
  AND s.deleted_at IS NULL
  AND g.deleted_at IS NULL
```

> `spaces.owner_type`으로 개인/그룹 분기를 먼저 판단하면 한쪽 경로만 탐색 가능.

---

## 이전 설계 대비 변화

| 이전 | 이후 | 이유 |
|------|------|------|
| `spaces.type ENUM('personal','group')` | 제거 | Space는 순수 컨테이너, 타입 분기 없음 |
| `space_members` | → `group_members` | 개인 공간에 멤버십 개념 없음 |
| `spaces.settings JSONB` | → `groups` 컬럼들로 분리 | 그룹 설정은 Group 도메인 |
| `users.personal_space_id` | 복원. UNIQUE 추가 | 소유자→Space 단방향. spaces는 소유자 모름 |
| `users.learning_style` | → `users.default_strategy_id` | Strategy 도메인으로 분리 |
| `space_members.role` | → `group_members.role` | 역할은 그룹 컨텍스트에서만 의미 있음 |
