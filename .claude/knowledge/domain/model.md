# 도메인 모델 — P/C/M/D

## 노드 타입 (4계층)

| 타입 | 접두사 | 정의 | 예시 |
|------|--------|------|------|
| Principle | `P:` | 도메인 독립 보편 원리 | `P:time-space-tradeoff` |
| Concept | `C:` | 원리가 특정 영역에서 구체화 | `C:caching` |
| Manifestation | `M:` | 구체적 기술·도구·현상 | `M:it/infrastructure/redis` |
| Domain | `D:` | 지식 영역 분류 축 | `D:computer-science` |

**접두사(P:/C: 등)는 UI 표시용, DB 식별자 아님** — `node_type` 컬럼 + `label` 컬럼으로 저장.

## 노드 식별자 정책

```
PK: UUID (불변 — node_type 승격/강등 시에도 UUID 유지)
label: kebab-case 정규화 저장 (e.g. "time-space-tradeoff")
display_name: 원본 표기 별도 저장 (e.g. "Time-Space Tradeoff")
unique: (space_id, node_type, label)
```

## 6종 관계

| 관계 | 방향 | 의미 |
|------|------|------|
| `DECOMPOSE_TO` | C → P | 이 개념은 이 원리로 분해된다 |
| `MANIFESTS_AS` | P → C | 이 원리가 이 개념으로 나타난다 |
| `INSTANTIATED_BY` | C → M | 이 개념이 구체적 형태로 나타난다 |
| `CONNECTS_TO` | C → C | 직접적 관계 (의존·보완·확장) |
| `ANALOGOUS_TO` | C → C | 구조적 유사성 (다른 도메인) |
| `BELONGS_TO` | C → D | 이 개념은 이 영역에 속한다 |

※ `node_lineage` (공간 간 이동 계보)는 별도 테이블 — 6종 의미 관계와 분리.

## 진입 기준 (승격/강등 판정)

**P 진입 조건** (셋 다 충족):
1. 3개+ 분야에서 등장
2. 더 단순한 원리로 분해 불가
3. 트레이드오프 또는 불변 법칙 기술

**C 진입 조건** (셋 다 충족):
1. 1~2개 P로 분해 가능
2. 2개+ 서로 다른 기술/도구에서 등장
3. 기존 C의 스케일 변형이 아님

**미충족 시**: 기존 노드에 흡수 또는 강등 (C→M, P→C)

**중요**: P 노드 생성은 AI 제안 + **사용자 확정 게이트 필수** — 자동 확정 없음.

## 노드 상태

```
draft      LLM이 추출한 후 사용자 리뷰 대기
confirmed  사용자가 확정
rejected   사용자가 거부
```

## DB 스키마 (nodes 테이블 핵심)

```sql
nodes
  id            UUID PK
  space_id      UUID          -- FK 없음, 애플리케이션 레벨 검증
  node_type     ENUM('P','C','M','D')
  label         VARCHAR       -- kebab-case 정규화
  display_name  VARCHAR       -- 원본 표기
  description   TEXT
  status        ENUM('draft','confirmed','rejected')
  embedding     vector(1536)  -- 비동기 생성, Phase 1-A부터 컬럼 예약
  created_by    UUID
  deleted_at    TIMESTAMPTZ   -- soft delete
  UNIQUE (space_id, node_type, label)
```
