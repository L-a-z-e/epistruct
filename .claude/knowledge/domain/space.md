# Space 모델 — 공간·멤버십·Node Proposal

## Space 타입

| 타입 | 설명 | 생성 |
|------|------|------|
| `personal` | 개인 지식 공간. 사용자당 1개 (앱 레벨 제한). | 회원가입 시 자동 생성 |
| `group` | 그룹 협업 공간. 여러 멤버. | 사용자가 명시적 생성 |

**is_public 플래그**: Space 타입과 독립.
- `false` (기본): 본인(personal) 또는 멤버(group)만 접근
- `true`: 외부인 읽기 가능. 단 가져가기는 항상 이해 게이트(재구성) 경유

## 스키마

```sql
spaces
  id          UUID PK
  type        ENUM('personal', 'group')
  name        VARCHAR
  is_public   BOOLEAN DEFAULT false
  created_by  UUID    -- 생성자 (불변, 감사 목적)
  settings    JSONB   -- 그룹 설정 (require_approval 등)
  created_at  TIMESTAMPTZ
  deleted_at  TIMESTAMPTZ

space_members
  space_id  UUID
  user_id   UUID
  role      ENUM('owner', 'admin', 'member', 'viewer')
  joined_at TIMESTAMPTZ
  PK: (space_id, user_id)
```

## 역할 권한

| 역할 | 권한 |
|------|------|
| `owner` | 공간 삭제, 모든 권한. 변경 가능(양도). space당 정확히 1명. |
| `admin` | 멤버 초대/제거/역할 변경. 노드 생성·편집·삭제. |
| `member` | 노드 생성·편집 (승인 정책에 따라 직접 반영 또는 제안). |
| `viewer` | 읽기만 가능. |

**권한 체크**: 공간 타입 분기 없이 `space_members.role`로 통일.

**owner 변경**: 기존 owner → 다른 역할 강등 + 신규 owner 승격 (application 레벨 트랜잭션).

## Node Proposal (그룹 승인 시스템)

`require_approval = true`일 때 `member`의 노드 변경은 제안으로 기록, owner/admin 승인 후 반영.

```sql
-- spaces.settings JSONB 구조
{
  "require_approval": false,                    -- false: 즉시 반영 (기본)
  "auto_approve_roles": ["owner", "admin"]      -- 이 역할은 승인 없이 즉시 반영
}

node_proposals
  id            UUID PK
  space_id      UUID
  proposed_by   UUID
  node_id       UUID NULL    -- null이면 새 노드 생성 제안
  action        ENUM('create', 'update', 'delete')
  payload       JSONB        -- 제안 노드 데이터
  status        ENUM('pending', 'approved', 'rejected')
  reviewed_by   UUID NULL
  reviewed_at   TIMESTAMPTZ NULL
  created_at    TIMESTAMPTZ
```

Node Proposal은 Phase 2 구현 대상. Phase 1-A에서는 스키마 껍데기만 생성.

## 공간 간 지식 이동 (재구성 게이트)

```
원본 노드(공개 공간)
  → AI 번역 제안 (대상 공간 맥락으로 변환, 보조)
  → 사용자 이해·정리 (필수 게이트: 직접 수정·재구성)
  → 대상 공간에 새 노드로 확정 저장
```

- 원본을 그대로 복사·참조하지 않는다 — 재구성 게이트가 LLM Wiki 안티패턴과의 차이.
- 새 노드는 `node_lineage` 테이블로 원본과 계보 연결 (Phase 2).

```sql
node_lineage
  id              UUID PK
  source_node_id  UUID    -- 원본 노드
  derived_node_id UUID    -- 재구성된 노드
  moved_by        UUID    -- 이동한 사용자
  moved_at        TIMESTAMPTZ
  -- Phase 3: diff 저장 추가
```
