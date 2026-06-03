# Epistruct

## 프로젝트 개요
AI 시대에 사람이 지식을 직접 인지·구조화하도록 돕는 개인화 지식 그래프 플랫폼.
핵심 철학: AI는 보조자(코치·번역가·원리 연결자), 사람이 루프의 주체.

## 현재 상태

| 항목 | 값 |
|------|-----|
| **Phase** | 1-A 착수 (개발 환경 완료, 백엔드 구현 시작) |
| **브랜치 전략** | main / dev 2단계. 상세 → `.claude/rules/git.md` |
| **체크리스트** | `docs/planning/CHECKLIST.md` |
| **다음 작업** | Phase 1-A 백엔드 구현 — 프로젝트 셋업 (Modular Monolith) |

## ⚠ 핵심
- **Git 규칙**: `.claude/rules/git.md` 준수 — 브랜치 생성·push·PR 모두 포함
- **모든 작업은 dev 기준 브랜치부터** — main/dev 직접 커밋 금지. push·PR은 사용자 명시 확인 후에만.

## 기술 스택
- **Frontend**: Expo (React Native + RN Web) — iOS/Android/Web 통합
- **Backend**: FastAPI (Modular Monolith) — `auth / knowledge / space / ai_pipeline`
- **DB**: PostgreSQL 18 + pgvector 0.8.2 — `pgvector/pgvector:pg18` 이미지
- **Auth**: Supabase Auth + JWT 검증 (FastAPI 미들웨어)
- **AI**: Claude API + RAG (pgvector 기반)

## 빌드 & 실행

```bash
# 백엔드 DB 기동
cd epistruct-api && docker compose up -d

# 백엔드 실행 (Phase 1-A 착수 후 갱신)

# 프론트엔드 실행
cd epistruct-app && pnpm start
```

## 도메인 모델 요약 (P/C/M/D)
- **P (Principle)**: 도메인 독립 보편 원리 — 3개+ 분야 등장, 더 단순한 원리로 분해 불가
- **C (Concept)**: 원리가 특정 영역에서 구체화 — 1~2개 P로 분해, 2개+ 기술에서 등장
- **M (Manifestation)**: 구체적 기술·도구·현상
- **D (Domain)**: 지식 영역 분류 축
→ 상세: `.claude/knowledge/domain/model.md`

## 아키텍처 규칙
- **모듈 디렉토리 구조**: `domain/ services/ repositories/ router.py schemas.py` — 상세: `.claude/rules/module-structure.md`
- **모듈 경계**: 각 모듈은 자기 테이블만 직접 접근. 타 모듈 테이블 직접 JOIN 금지 — service layer 경유 필수
- **DB FK 없음**: UUID 참조만 보유, 참조 무결성은 application 레벨 — MSA 전환 용이성
- **Soft delete 필수**: 모든 주요 테이블 `deleted_at TIMESTAMPTZ` — 물리 DELETE 없음
- **API 분리**: `/api/v1/` 외부(breaking change 금지·버전 관리) vs `/internal/` 내부(자유 변경)
→ 상세: `.claude/knowledge/domain/architecture.md`

## 노드 상태 흐름
`draft` → 사용자 리뷰 → `confirmed` | `rejected`
- **P 노드**: AI 제안 + 사용자 확정 게이트 필수 — 자동 확정 없음
→ 상세: `.claude/knowledge/domain/pipeline.md`

## 브랜치 규칙
→ `.claude/rules/git.md` 준수. main/dev 2단계 전략, push·PR은 사용자 명시 확인 후에만.

## 협업 방식 (학습 병행 개발)
- **설명 먼저, 코드 나중**: 새 프레임워크·언어·아키텍처 개념 등장 시 "왜 + 어떤 원리로" 먼저 설명
- **결정 이유 공유**: 여러 선택지가 있을 때 옵션과 트레이드오프 제시 후 사용자 선택 — 블랙박스 결정 금지
- **진행 중 질문 환영**: "왜?", "이게 뭐야?" 질문 시 작업 멈추고 충분히 설명
- **체크리스트 기준**: `docs/planning/CHECKLIST.md`. 각 항목 착수 전 해당 섹션 함께 확인

## 핵심 규칙
- 에러 발생 시: 에러 전문 + 관련 코드 최소 1파일 Read 후 수정 — 분석 없는 수정 금지
- 기능 미동작 시 삭제 금지. 3회 미해결 시 사용자에게 상황 보고 — 삭제는 해결이 아님
- 문자열 리터럴 2회+ 반복 시 상수/환경변수 추출 — 변경점 추적 불가 방지

## 검증 원칙
- 테스트 실행 주장 시 실제 Bash 출력 확인 필수 — 미실행 시 "미실행" 명시
- 확인 불가 사항(외부 서비스, 프로덕션 동작) → "확인 불가" 명시

## 절대 금지
- main 직접 커밋·푸시 (사용자 허가 없이)
- 타 모듈 DB 테이블 직접 JOIN (service layer 우회)
- 물리 삭제 (`DELETE FROM` — soft delete 사용)
- P 노드 자동 확정 (사용자 확정 게이트 필수)

## 런타임 버전 (확정)

| 런타임 | 버전 | 고정 파일 |
|--------|------|----------|
| Python | 3.12 | `.python-version` |
| Node.js | 24 LTS | `.nvmrc` |
| PostgreSQL | 18 | `docker-compose.yml` (`pgvector/pgvector:pg18`) |
| pgvector | 0.8.2 | `docker-compose.yml` |

→ 버전 변경 절차: `.claude/knowledge/decisions/runtime-versions.md`

## 배포 아키텍처 (확정)
- **개발**: 로컬 Docker Compose (`epistruct-api/docker-compose.yml`)
- **배포**: AWS ECS Fargate (서비스별 독립 Task)
- **DB**: RDS PostgreSQL 18 + pgvector
- **모니터링**: Prometheus + Grafana + Loki + GlitchTip
- **LLM 관찰성**: Langfuse 클라우드 무료 플랜
- **알림**: Telegram + Discord (Phase 1-A)

→ 상세: `.claude/knowledge/decisions/infra-deployment.md`

## 참조 (Knowledge Base)
- `.claude/knowledge/domain/` — 도메인 모델·아키텍처·파이프라인·인증·스페이스
- `.claude/knowledge/decisions/` — 기술 결정 기록 (runtime-versions, api-design-conventions, infra-deployment)
- `.claude/knowledge/errors/` — 에러 패턴 기록
- `.claude/knowledge/patterns/` — 코드·운영 패턴 기록
- `.claude/rules/api-design.md` — API 명세 작성·검토 체크리스트 (API 설계 요청 시 반드시 읽기)
