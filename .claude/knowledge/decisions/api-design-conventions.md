---
type: decision
tags: [api, rest, graphql, grpc, sse, polling, error-format, versioning]
created: 2026-06-02
status: active
---

# API 설계 규약 결정

## 선택

| 항목 | 결정 |
|------|------|
| 외부 API 구조 | REST (`/api/v1/`) + GraphQL (`/graphql`) 완전 분리 |
| 내부 통신 | gRPC 인터페이스 Phase 1부터 정의 (구현은 함수 호출, MSA 전환 시 교체) |
| AI 파이프라인 비동기 | Polling 기본 (HTTP 202 + job_id), SSE 선택적 (LLM 텍스트 스트리밍만) |
| 에러 응답 형식 | RFC 7807 필드명 차용 + `code` 확장 (`type` URI는 Phase 2 공개 API 전환 시 추가) |
| 응답 Envelope | 항상 사용 — 단일/목록 모두 `{"data": ..., "meta": ...}` |
| 페이지네이션 | Cursor 기반 (`after`, `before`, `limit`) |
| 날짜 형식 | ISO 8601 + UTC (`"2026-06-02T09:00:00Z"`) |
| API 버저닝 | URL 버저닝 (`/api/v1/`) + Breaking change 기준 명시 |

## 이유

**REST + GraphQL 분리**
Knowledge 그래프 조회는 "노드 + 관계 + 소스를 한 번에" 가져와야 하는 패턴이 많다.
REST로 구현하면 여러 번 요청하거나 응답 과잉이 발생한다.
GraphQL은 클라이언트가 필요한 필드만 지정할 수 있어 그래프 조회에 적합.
단순 CRUD(인증, Space/Group)는 REST가 명확하고 캐싱에 유리하다.

**Polling 기본 + SSE 선택**
- Expo(모바일) 환경에서 SSE는 EventSource 미지원 → `react-native-sse` 폴리필 필수
- SSE는 인프라(nginx, Envoy) 타임아웃 설정 필요 — 초기에 함정이 많음
- AI 임베딩 생성처럼 "중간은 조용하고 끝만 중요한" 작업은 Polling이 자연스럽다
- LLM 토큰 스트리밍처럼 "점진적 출력"이 있을 때만 SSE 적용
- Polling은 Stateless → 수평 확장 쉬움, 모바일 배터리 친화적

**RFC 7807 필드명 차용 (type URI 없이)**
- 완전한 RFC 7807은 `type` URI를 실제 운영해야 함 (에러 타입별 문서 URL)
- 초기 스타트업에서 이 URL 관리는 실질적 오버헤드
- `code` 필드는 클라이언트 switch 분기 처리에 직접 사용 가능
- `instance`, `trace_id` 필드로 디버깅과 로그 연계는 충분히 확보
- 나중에 `type` 추가해도 non-breaking change

**항상 Envelope 사용**
- 나중에 단일 리소스에 `meta` 추가 필요할 때 non-breaking change
- Expo 앱은 버전 강제 업데이트가 어렵기 때문에 응답 형식 안정성이 중요
- 성공/에러 모두 최상위 키 보면 구조 파악 가능

## 대안 검토

| 대안 | 기각 이유 |
|------|----------|
| WebSocket | LLM 스트리밍은 단방향. 양방향성 불필요. 방화벽 차단 위험 |
| Webhook | 모바일 클라이언트(NAT/방화벽)에는 서버가 도달 불가 |
| GraphQL 전체 통일 | auth, space 같은 단순 CRUD에 GraphQL 오버스펙. 캐싱 어려움 |
| 완전한 RFC 7807 | `type` URI 관리 비용. 현재 단계에서 불필요한 오버헤드 |
| Envelope 없음 | 단일 리소스에 meta 추가 시 breaking change 위험 |

## 관련

- `docs/design/api-spec.md` — 전체 API 명세
- `docs/design/erd-ddd.md` — 도메인 모델
- `rules/api-design.md` — 명세 작성 시 체크리스트
