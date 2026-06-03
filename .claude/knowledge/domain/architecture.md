# 아키텍처 규칙

## 모듈 구조

```
epistruct-api/
├── auth/           JWT 검증 미들웨어 + users 프로필 (인증 자체는 Supabase 위임)
├── knowledge/      nodes + node_relationships + 그래프 조회 (핵심 도메인)
├── space/          spaces + space_members + Node Proposal
└── ai_pipeline/    LLM + 임베딩 + 노드 추출 파이프라인
```

## 모듈 경계 규칙 (엄격)

```
✅ 허용
  - 각 모듈은 자기 테이블만 직접 쿼리
  - 타 모듈 데이터가 필요하면 해당 모듈의 service layer 함수 호출

❌ 금지
  - 타 모듈 테이블 직접 JOIN (e.g. knowledge 모듈에서 spaces 테이블 직접 JOIN)
  - 타 모듈 테이블 직접 INSERT/UPDATE/DELETE
```

이유: 모듈 경계를 지켜야 MSA 분리 시 코드 이동이 가능하다.

## DB 설계 원칙

### FK 없음
```sql
-- ❌ 금지
nodes.space_id UUID REFERENCES spaces(id)

-- ✅ 올바름
nodes.space_id UUID  -- 참조 무결성은 service layer에서 보장
```
이유: DB FK는 MSA 전환 시 분리를 막는 강결합.

### Soft Delete 필수
```sql
-- 모든 주요 테이블
deleted_at TIMESTAMPTZ  -- NULL이면 활성, 값 있으면 삭제됨

-- 조회 시 항상 필터
WHERE deleted_at IS NULL

-- 물리 삭제 절대 금지
DELETE FROM nodes ...  -- ❌
UPDATE nodes SET deleted_at = NOW() ...  -- ✅
```

### Outbox Pattern (상태 변경 이벤트)
- 상태 변경은 Outbox Pattern으로 이벤트 유실 방지
- MSA 전환 시 이벤트 버스 연결 기반

## API 분리 원칙

```
/api/v1/    외부 연계용 공개 API
            - breaking change 불가
            - 버전 관리 필수
            - 스펙 변경 시 /api/v2/ 추가

/internal/  모듈 간 내부 호출용
            - 자유롭게 변경 가능
            - 외부 노출 없음
```

## MSA 분리 트리거 (사전 정의)

| 모듈 | 분리 조건 |
|------|----------|
| `ai_pipeline` | LLM 비용 > 운영비 30%, 또는 응답 지연이 핵심 UX에 영향 |
| `knowledge` | DAU 10,000 초과, 또는 팀이 도메인별로 분리될 때 |

## LLM structured output 스키마 (노드 추출)

```json
{
  "node_type": "P|C|M|D",
  "label": "kebab-case-label",
  "display_name": "원본 표기",
  "description": "설명",
  "relationships": [
    {
      "relation": "DECOMPOSE_TO|MANIFESTS_AS|...",
      "target_label": "대상 노드 label"
    }
  ]
}
```
- structured output(JSON schema) 강제 — 자유 텍스트 응답 없음
- 추출 결과는 `draft` 상태로만 저장
