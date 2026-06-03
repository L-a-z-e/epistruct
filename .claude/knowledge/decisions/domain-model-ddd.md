---
type: decision
tags: [ddd, domain-model, database-schema, space, group, bounded-context]
created: 2026-06-02
status: active
---

# DDD 기반 4개 Bounded Context 도메인 분리

## 선택

4개 Bounded Context로 분리:
- **User Domain**: `users` (personal_space_id UNIQUE → spaces.id)
- **Space Domain**: `spaces`, `nodes`, `node_relationships`, `sources`, `chunks`, `node_sources`, `node_lineage`
- **Group Domain**: `groups` (space_id UNIQUE → spaces.id), `group_members`, `node_proposals`
- **Strategy Domain**: `learning_strategies`

소유 방향: **소유자 → Space** 단방향.
`spaces` 테이블은 소유자 ID 없음. `owner_type ENUM('personal','group')` 힌트 컬럼만 보유 (반정규화).

## 이유

**`space_members`의 이중 역할 해소**: 기존 설계에서 `space_members`는 개인 공간(1명)과 그룹 공간(여러 명)을 동시에 처리했음. "개인 공간에 왜 members 테이블이 있지?"라는 개념 불일치 발생. → 멤버십 개념은 Group 도메인(`group_members`)으로 완전 분리.

**Space는 순수 컨테이너**: Space의 책임은 노드/소스를 담는 것뿐. 소유 관계는 소유자 도메인의 책임. `spaces.user_id`나 `spaces.group_id`를 두면 spaces가 소유자를 알아야 하는데, 이는 도메인 경계 위반.

## 대안 검토

| 대안 | 거절 이유 |
|------|-----------|
| `spaces.type ENUM('personal','group')` 유지 | Space가 타입별로 다르게 동작하는 것처럼 보임. 순수 컨테이너 원칙 위반 |
| `space_members`로 개인/그룹 통합 | 개인 공간에 멤버십 개념 불필요. 이중 역할 혼란 |
| `spaces.user_id` + `spaces.group_id` nullable | 순환 참조(groups.space_id ↔ spaces.group_id) 위험. 둘 중 하나만 값이 있다는 조건을 application이 보장해야 함 |
| `spaces.user_id` nullable (그룹 공간이면 NULL) | spaces만으로 소유자 파악 불가. groups 역조회 필요하면서도 spaces에 불완전한 소유 정보가 남음 |

## 트레이드오프

**얻는 것:**
- 도메인 경계 명확 — 각 도메인이 독립적으로 진화 가능
- Space는 진짜 순수 컨테이너
- 개인/그룹 소유 관계가 각 도메인 테이블에서 명시적으로 드러남

**잃는 것:**
- "내가 접근할 수 있는 모든 공간" 조회 시 UNION 필요 (두 경로: users.personal_space_id, groups→group_members)
- spaces만으로 소유자 파악 불가 → `owner_type`으로 완화

## 소유권 유일성 보장

```sql
users.personal_space_id  UNIQUE  -- 한 space는 한 user만 소유
groups.space_id          UNIQUE  -- 한 space는 한 group만 소유
```

user와 group이 동시에 같은 space 참조하는 경우는 application 레벨 보장 (생성 시점에 분기되므로 실제 발생 가능성 낮음).

## "내가 접근할 수 있는 모든 공간" 조회 패턴

```sql
SELECT s.id FROM spaces s
JOIN users u ON u.personal_space_id = s.id
WHERE u.id = $user_id AND s.deleted_at IS NULL

UNION

SELECT s.id FROM spaces s
JOIN groups g ON g.space_id = s.id
JOIN group_members gm ON gm.group_id = g.id
WHERE gm.user_id = $user_id
  AND s.deleted_at IS NULL
  AND g.deleted_at IS NULL
```

`spaces.owner_type`으로 분기 시 한쪽 경로만 탐색 가능.

## 관련

- `docs/design/erd-ddd.md` — 전체 테이블 정의
- `docs/prd/Epistruct_PRD_v0.7.md` — 5.6, 8.5 섹션
- `.claude/knowledge/domain/space.md` — Space 도메인 상세
