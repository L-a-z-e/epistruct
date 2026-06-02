# LLM 노드 추출 Structured Output 스키마

> 버전: v1.0  
> 작성일: 2026-06-02  
> 관련 문서: `docs/design/erd-ddd.md`, `docs/design/ux-node-review.md`

---

## 1. 개요

소스(URL/PDF/YouTube/텍스트)에서 지식 노드와 관계를 추출하는 LLM 호출 명세.  
Claude API structured output을 사용해 JSON 스키마를 강제한다.

**Phase 1-A 추출 대상**

| 항목 | 대상 | 제외 |
|------|------|------|
| 노드 타입 | C, M, D | P (Phase 1-B) |
| 관계 타입 | INSTANTIATED_BY, CONNECTS_TO, BELONGS_TO | DECOMPOSE_TO, MANIFESTS_AS, ANALOGOUS_TO |

---

## 2. 호출 전략

```
소스 토큰 수 계산
    │
    ├── 120K 이하 → 소스 전체를 1회 호출
    │
    └── 120K 초과 → N개 청크씩 배치 호출 후 서버에서 합산·중복 제거
```

120K 기준: 시스템 프롬프트 + 응답 공간을 제외한 실질 소스 입력 한도.  
배치 크기: 청크 단위로 나누되 배치당 100K 토큰 이하 유지.

---

## 3. 시스템 프롬프트 구조

```
[역할]
당신은 학습 자료에서 지식 구조를 추출하는 전문가입니다.
사용자가 지식을 직접 인지하고 통제할 수 있도록, 핵심 개념과 관계만 추출합니다.
AI가 판단을 대신하지 않습니다 — 추출 결과는 사용자가 검토하고 확정합니다.

[노드 타입 기준]
- C (Concept): 2개 이상 기술/맥락에 등장하는 구체적 개념. 예: "useMemo", "캐싱", "의존성 주입"
- M (Manifestation): 특정 도구·언어·프레임워크의 구체적 구현체. 예: "React.memo", "redis-py", "@Injectable()"
- D (Domain): 이 자료가 속하는 지식 영역. 예: "React", "운영체제", "강화학습"

[추출 규칙]
- 노드는 사용자가 독립적으로 이해할 수 있는 단위로 추출한다
- 자료에 명시적으로 등장하는 내용만 추출한다 — 추론·확장 금지
- 같은 개념이 여러 번 등장해도 노드는 1개만 추출한다
- description은 2-4문장으로, 정의·동작 원리·활용 맥락을 포함한다
- confidence는 해당 노드/관계가 추출 기준에 얼마나 부합하는지 (0.0-1.0)
  - 0.9 이상: 기준 충족 확실
  - 0.7-0.9: 기준 충족 가능성 높음
  - 0.7 미만: 불확실, 사용자 판단 필요

[관계 타입]
- INSTANTIATED_BY: 개념(C)이 구체적 구현체(M)로 나타날 때. 방향: C → M
- CONNECTS_TO: 개념 간 직접적 관련(의존·보완·확장). 방향: C → C
- BELONGS_TO: 개념이 특정 도메인에 속할 때. 방향: C → D
```

---

## 4. JSON 스키마

### 4.1 출력 스키마 정의

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["domain_suggestions", "nodes"],
  "properties": {
    "domain_suggestions": {
      "type": "array",
      "description": "이 자료가 속하는 도메인 후보. 복수 도메인 가능.",
      "items": {
        "type": "object",
        "required": ["name", "confidence"],
        "properties": {
          "name":       { "type": "string", "description": "도메인 이름 (원문 그대로)" },
          "confidence": { "type": "number", "minimum": 0, "maximum": 1 }
        }
      }
    },
    "nodes": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["node_type", "label", "description", "confidence"],
        "properties": {
          "node_type":     { "type": "string", "enum": ["C", "M", "D"] },
          "label":         { "type": "string", "description": "노드 이름 (원문 그대로)" },
          "description":   { "type": "string", "description": "2-4문장. 정의·동작 원리·활용 맥락 포함" },
          "confidence":    { "type": "number", "minimum": 0, "maximum": 1 },
          "relationships": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["type", "target_label", "confidence"],
              "properties": {
                "type": {
                  "type": "string",
                  "enum": ["INSTANTIATED_BY", "CONNECTS_TO", "BELONGS_TO"]
                },
                "target_label": {
                  "type": "string",
                  "description": "관계 대상 노드의 label. 반드시 nodes 배열 내 label 또는 domain_suggestions의 name 중 하나."
                },
                "confidence": { "type": "number", "minimum": 0, "maximum": 1 }
              }
            }
          }
        }
      }
    }
  }
}
```

### 4.2 출력 예시

```json
{
  "domain_suggestions": [
    { "name": "React", "confidence": 0.97 },
    { "name": "Frontend 성능 최적화", "confidence": 0.81 }
  ],
  "nodes": [
    {
      "node_type": "C",
      "label": "useMemo",
      "description": "의존성 배열의 값이 변경될 때만 함수를 재실행하고 결과를 캐시하는 React Hook이다. 렌더링마다 반복되는 비용이 큰 계산을 건너뛰어 성능을 최적화한다. useCallback과 함께 사용하면 자식 컴포넌트의 불필요한 리렌더링도 방지할 수 있다.",
      "confidence": 0.94,
      "relationships": [
        { "type": "CONNECTS_TO",      "target_label": "useCallback", "confidence": 0.88 },
        { "type": "CONNECTS_TO",      "target_label": "메모이제이션", "confidence": 0.91 },
        { "type": "BELONGS_TO",       "target_label": "React",        "confidence": 0.97 }
      ]
    },
    {
      "node_type": "C",
      "label": "메모이제이션",
      "description": "이전에 계산한 결과를 저장해두고 동일한 입력이 들어오면 재계산 없이 캐시된 값을 반환하는 최적화 기법이다. 시간 복잡도와 공간 복잡도를 맞바꾸는 트레이드오프가 있다.",
      "confidence": 0.89,
      "relationships": [
        { "type": "BELONGS_TO", "target_label": "Frontend 성능 최적화", "confidence": 0.82 }
      ]
    },
    {
      "node_type": "M",
      "label": "React.memo",
      "description": "컴포넌트를 래핑하여 props가 변경되지 않으면 리렌더링을 건너뛰는 React 고차 컴포넌트(HOC)다. 얕은 비교(shallow compare)로 props 변경을 감지한다.",
      "confidence": 0.92,
      "relationships": [
        { "type": "INSTANTIATED_BY", "target_label": "useMemo",   "confidence": 0.79 },
        { "type": "BELONGS_TO",      "target_label": "React",      "confidence": 0.96 }
      ]
    }
  ]
}
```

---

## 5. 서버 처리 규칙

### 5.1 도메인 처리 (D 노드)

```
LLM domain_suggestions 수신
    │
    ├── Space 내 기존 D 노드 목록과 이름 비교 (대소문자 무시)
    │       ├── 일치하는 D 노드 있음 → "기존 도메인" 후보로 제시
    │       └── 없음 → "새 도메인" 후보로 제시
    │
    └── 리뷰 화면에서 사용자 확정
            ├── 기존 D 노드 선택
            ├── AI 제안 이름으로 새 D 노드 생성
            └── 직접 이름 입력 후 생성
```

### 5.2 노드 저장

- 모든 노드는 `status = draft`로 저장
- `label` unique 제약: `(space_id, node_type, label)` 대소문자 무시
  - 이미 존재하는 label이면 새로 생성하지 않고 기존 노드에 연결
- `confidence` 필드는 DB 저장 (리뷰 화면 UI 강조에 활용)

### 5.3 관계 처리

- `target_label`이 같은 추출 결과 내 nodes 배열에 없으면 관계 저장 보류
- 노드 확정(confirmed) 후 양쪽 노드가 모두 confirmed일 때 관계 활성화
- 관계도 `status = draft`로 저장, 노드 카드 리뷰 화면에서 함께 확정

### 5.4 배치 fallback 중복 제거

소스가 120K 초과로 배치 처리된 경우:
- 배치별 결과를 합산 후 `(node_type, label)` 기준 중복 제거 (대소문자 무시)
- 중복된 경우 confidence가 높은 쪽 채택, description은 더 긴 쪽 채택
- 관계도 중복 제거 (`from_label`, `type`, `target_label` 기준)

---

## 6. confidence 활용 기준

| confidence | 리뷰 화면 표시 |
|-----------|--------------|
| 0.9 이상  | 기본 스타일 |
| 0.7–0.9  | 주의 아이콘 (⚠) |
| 0.7 미만  | 황색 강조 + "AI가 확신하지 못합니다" 레이블 |

사용자는 어떤 confidence의 노드도 수락·거부·편집할 수 있다. confidence는 참고용이며 자동 필터링에 사용하지 않는다.
