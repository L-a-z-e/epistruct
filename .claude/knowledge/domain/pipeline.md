# 데이터 파이프라인 — Source → Chunk → Node

## 3계층 구조

```
Layer 1: Source (원본)
  사용자가 넣은 것. 사람이 읽기 위해 보존.
  타입: url | pdf | youtube | text | conversation

      ↓ 청킹(chunking)

Layer 2: Chunk (가공본)
  AI가 처리하는 단위. 임베딩 저장. RAG 기반.
  embedding vector(1536) 컬럼 보유.

      ↓ LLM 추출 + 사용자 확정 (필수 게이트)

Layer 3: Node (지식)
  P/C/M/D. 사용자가 확정한 구조화된 이해.
```

**레이어 독립성**: 상위 레이어 삭제 시 하위 레이어 유지. Source 삭제 → Node 유지.

## 처리 흐름

```
1. Source 저장 (동기)
2. Chunk 분할 (동기)
3. 임베딩 생성 (비동기 BackgroundTask)
4. LLM 노드 후보 추출 (structured output JSON)
5. draft 상태로 저장
6. 사용자 리뷰 화면 제공
7. 사용자 수정·확정(confirmed) 또는 거부(rejected)
8. Node + 관계 확정 저장 (동기)
```

## 노드 상태 흐름

```
draft ──→ confirmed
      └─→ rejected
```

- `draft`: LLM 추출 직후, 사용자 리뷰 대기
- `confirmed`: 사용자 확정 완료, 그래프에 반영
- `rejected`: 사용자 거부, 그래프 미반영 (soft delete 아님, 상태값으로 보존)

**P 노드**: AI 제안 + 사용자 확정 게이트 필수. 자동 confirmed 전환 없음.

## Source 타입별 처리

| type | 저장 방식 | 비고 |
|------|----------|------|
| `url` | URL + 크롤링 텍스트 | 원본 사이트 소멸 대비 텍스트 보존 |
| `pdf` | S3 파일 참조 + 추출 텍스트 | |
| `youtube` | URL + 자막 텍스트(yt-dlp) | 영상 자체 저장 불가 |
| `text` | 입력 텍스트 그대로 | |
| `conversation` | AI 대화 전체 JSON | |

## 관계 테이블 구조

```
Source → Chunk: 1:N
Chunk → Node: N:M (node_sources 브릿지 테이블)
```

```sql
node_sources
  node_id    UUID
  source_id  UUID
  chunk_id   UUID NULL
  PK: (node_id, source_id)
```

사용자가 직접 생성한 Node는 Source 없이도 존재 가능.

## 임베딩 전략

- Chunk 테이블 + Node 테이블 모두 `embedding vector(1536)` 예약 (Phase 1-A부터)
- 임베딩 생성: 비동기 (BackgroundTask) — Node 저장 블로킹 없음
- 활용: 중복 감지(F7), 능동 제안(F6), 원리 전이(F9)의 공통 기반 (Phase 1-B)
