# Epistruct 개발 체크리스트

> 마지막 업데이트: 2026-06-04 (Supabase Auth 연동 + webhook + F0 프로필 엔드포인트 완료)
> 기준 문서: [PRD v0.9](../prd/Epistruct_PRD_v0.7.md)

---

## 개발 환경 준비

> Phase 1-A 착수 전 로컬 환경 세팅. IDE → 런타임 → DB 순서로 진행.
> 패키지 구조 기준: [docs/design/package-structure.md](../design/package-structure.md)

### IDE — PyCharm + WebStorm + DataGrip

- [x] PyCharm Professional 설치 (백엔드)
  - [x] Python 플러그인 활성화 (기본 내장) — 프로젝트 생성 후 확인
  - [x] `.env` 파일 자동 인식 확인 (EnvFile 플러그인 or 내장) — 프로젝트 생성 후 확인
- [x] WebStorm 설치 (프론트엔드)
  - [x] Expo / React Native 지원 — WebStorm 기본 내장 (별도 플러그인 불필요)
  - [x] ESLint + Prettier 연동 설정 — eslint.config.js + .prettierrc 생성, WebStorm 연동 완료
  - [x] `tsconfig.json`의 `@/` 절대경로 alias 인식 확인 — import/export 문에서 정상 인식
- [x] DataGrip 설치 (DB 전용 툴)
  - [x] PostgreSQL 18 데이터소스 연결 (`localhost:5432`)
  - [x] Docker 컨테이너 기동 후 연결 확인
  - [x] `.env` `DATABASE_URL` 기반 연결 설정
- [x] 공통 설정
  - [x] JetBrains 단축키 프로필 통일 (세 IDE 동일하게)
  - [x] Git 연동 확인 (PyCharm + WebStorm) — 브랜치 인식 확인

### 런타임

- [x] Python 3.12 설치 확인 — pyenv global 3.12.12, 버전 고정: `.python-version`
- [x] `uv` 설치 — 0.10.2
- [x] Node.js 24 LTS 설치 확인 — nvm default 24 (v24.14.1), 버전 고정: `.nvmrc`
- [x] pnpm 설치 확인 — 10.33.0
- [x] Expo CLI 설치 확인 — 56.1.13

### DB — Docker (PostgreSQL + pgvector)

> `docker compose up -d` / `docker compose down`으로 환경 단위 제어

- [x] Docker Desktop 설치 및 실행 확인 (`docker --version`)
- [x] `docker-compose.yml` 작성
  - [x] `pgvector/pgvector:pg18` 이미지 사용 (pgvector 0.8.2 포함 공식 이미지)
  - [x] 포트: `5432:5432`
  - [x] 볼륨 마운트: `postgres_data:/var/lib/postgresql` (PG18+ 경로 — 버전별 서브디렉토리 자동 생성)
  - [x] 환경변수: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` — `.env` 참조, 기본값 없음
  - [x] healthcheck 설정 (FastAPI 기동 시 DB 준비 완료 대기용)
- [x] `.env` 파일 구성 (`DATABASE_URL` 포함) — `.env.example` 기반 작성
- [x] `.env` `.gitignore` 등록 확인
- [x] 컨테이너 기동 확인: `docker compose up -d` — healthy
- [x] pgvector 확장 활성화
  - [x] `CREATE EXTENSION IF NOT EXISTS vector;` 실행
  - [x] `\dx` 로 vector 0.8.2 확인
- [x] DataGrip에서 PostgreSQL 연결 확인 (위 DataGrip 섹션 참조)

### 패키지 구조 확정

- [x] 패키지 구조 설계 완료 — [docs/design/package-structure.md](../design/package-structure.md)
  - [x] 백엔드: 모듈 우선 수직 슬라이스 (`src/modules/{domain}/domain|application|infrastructure|presentation`)
  - [x] 프론트엔드: Expo Router 분리 + feature 자체 완결 (`app/` 라우팅만, `src/features/` 로직)
  - [x] 모듈 간 통신: `gateway.py` (동기) + Domain Events (비동기)
  - [x] 모듈 경계 강제: `__init__.py` 공개 API + 아키텍처 테스트
- [x] 백엔드 프로젝트 스캐폴딩 생성 (디렉토리 뼈대) — `epistruct-api/`
- [x] 프론트엔드 프로젝트 스캐폴딩 생성 (디렉토리 뼈대) — `epistruct-app/`

---

## Phase 0 — 설계 결정사항

> 설계 및 개발 착수 전 확정이 필요한 항목들

### 아키텍처 결정
- [x] 아키텍처 전략 — Modular Monolith → MSA 점진 전환
- [x] DB FK 제거 — 애플리케이션 레벨 검증 + soft delete 기본
- [x] 인증 방식 — Supabase Auth 확정
- [x] 그래프 시각화 MVP 범위 — 웹 우선, 네이티브는 Phase 1-B 이월

### 데이터 모델 결정
- [x] 데이터 3계층 구조 — Source → Chunk → Node
- [x] 노드 테이블 구조 — 단일 `nodes` 테이블 + `node_type` enum
- [x] 노드 label 정책 — UUID PK + `(space_id, node_type, label)` unique + `display_name` 분리
- [x] Space 모델 — 개인/그룹 2종 + `is_public` 플래그
- [x] 그룹 권한 모델 — owner / admin / member / viewer
- [x] Node Proposal — 그룹 승인 시스템 (optional, `require_approval`)
- [x] Provenance 정책 — Phase 2 최소 기록, Phase 3 diff 추가

### 미결 (Phase 1-B 착수 전 결정)
- [ ] 학습 스타일 측정 알고리즘 (O1)
- [ ] 중복 감지 임베딩 유사도 임계값 (O2)
- [ ] 네이티브 그래프 시각화 전략

---

## Phase 1-A — 저장·구조화

> 목표: 첫 번째로 동작하는 서비스. 입력 → 노드 추출 → 그래프 확인 → 편집.

### 설계
- [x] ERD 작성 (`docs/design/erd-ddd.md` — DDD Bounded Context 기반 재설계 완료)
  - [x] `users` 테이블
  - [x] `spaces` 테이블 (순수 지식 컨테이너, `owner_type` 힌트 컬럼)
  - [x] `groups` + `group_members` 테이블 (`space_members` → DDD 리팩토링으로 Group 도메인 분리)
  - [x] `sources` 테이블 (url/pdf/youtube/text/conversation)
  - [x] `chunks` 테이블 (embedding vector 예약)
  - [x] `nodes` 테이블 (label/display_name/embedding 예약)
  - [x] `node_relationships` 테이블 (6종 관계)
  - [x] `node_sources` 브릿지 테이블
  - [x] `node_lineage` 테이블 (껍데기, Phase 2)
  - [x] `node_proposals` 테이블 (껍데기, Phase 2)
  - [x] `learning_strategies` 테이블 (Strategy 도메인 분리)
- [x] API 명세 초안 (`docs/design/api-spec.md`)
  - [x] auth 모듈 — REST: GET/PATCH/DELETE /auth/me, POST /auth/webhook
  - [x] knowledge 모듈 — GraphQL: node/nodes/graph Query + confirmNode/rejectNode/updateNode/deleteNode/createRelationship Mutation
  - [x] space 모듈 — REST: spaces CRUD, groups CRUD + group_members 관리
  - [x] ai_pipeline 모듈 — REST+Polling+SSE: POST /sources (HTTP 202), GET /jobs/:id (폴링), GET /jobs/:id/stream (SSE)
  - [x] 내부 gRPC 계약 — AuthService / SpaceService / KnowledgeService / PipelineService .proto 정의
- [x] 노드 추출 리뷰 UX 플로우 (draft → confirmed/rejected) — `docs/design/ux-node-review.md`
- [x] 노드 추출 LLM structured output 스키마 정의 — `docs/design/llm-extraction-schema.md`

### 백엔드 구현 (FastAPI)
- [x] 프로젝트 셋업 (Modular Monolith 구조)
- [x] PostgreSQL + pgvector 연결
- [x] Supabase Auth 연동 (JWT 검증 미들웨어)
- [x] Supabase webhook → users 테이블 자동 생성
- [x] F0: 인증 엔드포인트 (프로필 조회/수정)
- [ ] F1: 혼합 입력 처리
  - [ ] URL 크롤링 + 텍스트 추출
  - [ ] PDF 업로드 + 텍스트 추출
  - [ ] YouTube yt-dlp 자막 추출
  - [ ] 텍스트 직접 입력
- [ ] F2: 노드 추출 파이프라인
  - [ ] Source → Chunk 분할 (청킹)
  - [ ] LLM structured output 노드 후보 추출
  - [ ] draft 상태로 저장
  - [ ] 임베딩 생성 (비동기 BackgroundTask)
- [ ] F2: 노드 확정 API (confirmed/rejected)
- [ ] F3: 그래프 조회 API (노드 + 관계)
- [ ] F4: 노드 CRUD (편집/병합/soft delete)

### 프론트엔드 구현 (Expo)
- [ ] 프로젝트 셋업 (Expo + RN Web)
- [ ] Supabase Auth SDK 연동 (로그인/가입/로그아웃)
- [ ] F1: 입력 화면 (URL/PDF/YouTube/텍스트)
- [ ] F2: 노드 추출 리뷰 화면 (draft 확정/거부)
- [ ] F3: 그래프 시각화 (웹: react-force-graph)
- [ ] F3: 네이티브 리스트/트리 뷰 (그래프 대체)
- [ ] F4: 노드 편집 화면

### 검증
- [ ] E2E 시나리오 S1 동작 확인 (URL 입력 → 노드 확정 → 그래프)
- [ ] 노드 편집/삭제 동작 확인
- [ ] 임베딩 비동기 생성 확인

---

## Phase 1-B — 지능화

> 목표: AI 차별화 핵심 기능. 원리 추출, 전이, 능동 제안.

### 설계 (착수 전 결정 필요)
- [ ] 학습 스타일 측정 알고리즘 확정 (O1)
- [ ] 임베딩 유사도 임계값 확정 (O2)
- [ ] 원리 추출 프롬프트 설계 (5.3 진입 기준 반영)
- [ ] 능동 제안 트리거 조건 정의

### 구현
- [ ] F5: 온보딩 (학습 스타일·관심 도메인 파악)
- [ ] F6: 맥락 기반 능동 제안
- [ ] F7: 중복 감지 + 통합 제안 (임베딩 유사도)
- [ ] F8: 원리(P) 추출 (AI 제안 + 사용자 확정)
- [ ] F9: 원리 전이 제안 (`ANALOGOUS_TO`)
- [ ] F10: 소크라테스식 학습 상호작용
- [ ] 네이티브 그래프 시각화 (Skia 기반 또는 대안)

---

## Phase 2 — 그룹 + 지식 융합

> 목표: 그룹 공간, 공개 설정, 공간 간 지식 재구성.

### 설계 (착수 전 결정 필요)
- [ ] 그룹 동시 편집 동시성 모델 (낙관적 락 구체화) (O4)
- [ ] Node Proposal 상세 UX 플로우

### 구현
- [ ] F11: Space `is_public` 토글
- [ ] F12: 공간 간 노드 가져오기 (이해 게이트)
- [ ] F13: AI 지식 번역 (맥락 변환 제안)
- [ ] F14: 충돌·중복 감지 + 병합 제안
- [ ] F15: `node_lineage` provenance 기록
- [ ] F16: 그룹 공간 운영 (생성·멤버십·Node Proposal)

---

## Phase 3 — 집단 지성

> 목표: 커뮤니티 기반 지식 확장. Phase 2 데이터 누적 후 착수.

- [ ] F17: 집단 지식 그래프 시각화
- [ ] F18: 지식 격차 발견
- [ ] F19: 학습 경로 추천
- [ ] F20: 원리 전이 커뮤니티 + 기여도 측정

---

## 보안

> 기준: OWASP API Security Top 10 2023 + OWASP LLM Top 10 2025 + Epistruct 기술 스택 특화 항목
> 레퍼런스: [teamhide/fastapi-boilerplate](https://github.com/teamhide/fastapi-boilerplate), [benavlabs/FastAPI-boilerplate](https://github.com/benavlabs/FastAPI-boilerplate), [AtticusZeller/fastapi_supabase_template](https://github.com/AtticusZeller/fastapi_supabase_template)

### 인증 · 인가

- [ ] JWT 로컬 검증 필수 파라미터 적용
  - [ ] `algorithms=["HS256"]` 명시 — 생략 시 `alg:none` 공격 노출
  - [ ] `audience="authenticated"` 명시 — 서비스 간 토큰 재사용 차단
- [ ] FastAPI `Depends()` 패턴으로 JWT 주입 (전역 미들웨어 대신 라우트별 명시적 보호)
- [ ] Refresh token rotation 활성화 (Supabase Auth 설정)
- [ ] `service_role` 키 서버 사이드 전용 보관 — 클라이언트 코드·저장소 포함 절대 금지
- [ ] 로그인 실패 에러 메시지 일반화 (username enumeration 방지)
- [ ] RBAC: 역할별 접근 제어 `Depends()` 구현 (owner / admin / member / viewer)
- [ ] **API1 BOLA**: 모든 리소스 조회·수정·삭제 시 소유권 검증 dependency 적용
- [ ] **API3 Mass Assignment**: 입력 모델(CreateRequest)과 응답 모델(PublicResponse) Pydantic 분리
- [ ] (Phase 2+) JWKS(ES256) 마이그레이션 경로 구조적으로 열어두기

### 데이터베이스 보안 (RLS)

> CVE-2025-48757: Supabase RLS 기본값은 **비활성화** — 명시적으로 켜지 않으면 anon key로 전체 데이터 접근 가능

- [ ] 모든 주요 테이블 RLS 명시적 활성화 (`ALTER TABLE ... ENABLE ROW LEVEL SECURITY`)
  - [ ] `nodes`, `node_relationships`, `sources`, `chunks` 테이블 포함
  - [ ] `node_sources`, `node_lineage`, `node_proposals` 테이블 포함
- [ ] FastAPI DB dependency에서 `SET LOCAL app.current_user_id = ?` 주입 (트랜잭션마다)
- [ ] RLS 정책: `(select current_setting('app.current_user_id'))` 패턴 사용 (행마다 실행 방지)
- [ ] `SECURITY DEFINER` 함수 사용 금지 — RLS 완전 우회됨
- [ ] pgvector 임베딩 테이블 RLS 적용 (개인 지식 격리, LLM08 대응)
- [ ] RLS 정책 컬럼에 인덱스 추가 (user_id, space_id 등)
- [ ] 애플리케이션 레이어 필터 + RLS 이중 적용 (defense-in-depth)
- [ ] RLS 테스트: 다른 사용자 데이터 접근 차단 확인

### API 보안 (OWASP API Top 10)

- [ ] **Rate Limiting** — `slowapi` 또는 `fastapi-limiter` (Redis 기반)
  - [ ] 일반 엔드포인트: 100 req/min
  - [ ] AI 파이프라인 (`POST /sources`): 10 req/min
  - [ ] 인증 관련 엔드포인트: 5 req/min (IP + 이메일 복합 키)
- [ ] CORS: 프로덕션 `allow_origins=["*"]` 금지 — 허용 도메인 명시적 열거
- [ ] Security Headers 미들웨어 일괄 적용
  - [ ] `Content-Security-Policy` (XSS 방어 핵심)
  - [ ] `Strict-Transport-Security` (HSTS)
  - [ ] `X-Content-Type-Options: nosniff`
  - [ ] `X-Frame-Options: DENY`
- [ ] SQL Injection: SQLAlchemy ORM / asyncpg 파라미터화 쿼리 — Raw SQL에 사용자 입력 직접 연결 금지
- [ ] XSS: HTML 입력 살균 (`nh3` 라이브러리 — `bleach` 대체)
- [ ] **SSRF**: 사용자 제공 URL 크롤링 시 내부 IP 범위 차단
  - [ ] `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16` 블락
- [ ] GraphQL: Query depth limit + complexity limit 적용 (Strawberry GraphQL Armor 또는 수동 구현)
- [ ] Webhook (`POST /auth/webhook`): HMAC-SHA256 서명 검증

### AI 파이프라인 보안 (OWASP LLM Top 10 2025)

- [ ] **LLM01 Prompt Injection 방어**
  - [ ] 외부 콘텐츠(크롤링, PDF, YouTube 자막) → `tool_result` 블록으로만 프롬프트 전달
  - [ ] 외부 텍스트 JSON 인코딩 래핑 — 데이터/지시 경계 강화
  - [ ] (선택) Harmlessness Screen: Claude Haiku 4.5로 입력 사전 스크리닝
- [ ] **LLM06 Excessive Agency 방지**
  - [ ] AI 파이프라인 최소 권한 원칙 — 불필요한 DB 쓰기 권한 제거
  - [ ] P 노드 자동 확정 금지 (사용자 확정 게이트 필수 — 기존 아키텍처 규칙)
- [ ] **LLM07 System Prompt Leakage 방지**
  - [ ] 시스템 프롬프트가 응답에 반영되지 않도록 출력 검증
- [ ] **LLM08 RAG 파이프라인 보안**
  - [ ] 임베딩 저장 전 콘텐츠 검증 (벡터 DB 중독 방지)
  - [ ] pgvector 유사도 검색 결과에 RLS 필터 적용 확인
- [ ] **LLM10 Unbounded Consumption 방지**
  - [ ] Claude API 호출 per-user Rate limiting
  - [ ] 최대 입력 토큰 제한 설정 (소스 입력 크기 제한)
  - [ ] LLM 비용 이상 급증 알림 설정
- [ ] AI 파이프라인 출력 JSON Schema 검증 (`llm-extraction-schema.md` 기준)

### 비밀 관리

- [x] `.env` `.gitignore` 등록 확인 (기존 항목 — 재확인)
- [x] `SUPABASE_JWT_SECRET`, `ANTHROPIC_API_KEY` 환경변수 관리
- [ ] 개발 / 스테이징 / 프로덕션 환경별 별도 API 키 운영
- [ ] Secrets Scanner CI 통합 (git-secrets 또는 trufflehog)

### 보안 테스트

- [ ] 인증 우회 시도 단위 테스트 (토큰 없음 / 만료 / 변조 / `alg:none`)
- [ ] BOLA 테스트: 다른 사용자 리소스 접근 시도 → 403 확인
- [ ] RLS 테스트: 다른 사용자 데이터 격리 DB 레벨 확인
- [ ] Rate Limit 동작 확인 (429 응답)
- [ ] SSRF 테스트: 내부 IP URL 크롤링 시도 차단 확인

---

## 인프라 / 운영

### 개발 환경 (로컬 Docker Compose)

- [x] 개발 환경 셋업 (docker-compose: PostgreSQL 18 + pgvector 0.8.2)
- [ ] CI/CD 파이프라인 구성
- [x] `.env.example` 파일 작성 (실제 값 제외한 키 목록)

### 배포 전략

> 현재: 로컬 개발/테스트 전용 → 향후: AWS 프리티어 → 실 사용자 유입 시 확장
> 상세 결정사항: `knowledge/decisions/infra-deployment.md` (미결, 리서치 후 작성)

- [ ] 로컬 Docker Compose → AWS 마이그레이션 경로 확정 (미결)
  - [ ] AWS 프리티어 한도 내 운영 가능 서비스 조합 결정
  - [ ] 인스턴스 시작/종료 자동화 방안 결정
- [ ] 스테이징 환경 구성

### 관찰성 스택 (Observability)

> 결정: 조합 B 풀스택. Docker Compose 서비스로 로컬부터 동일하게 구성.

**메트릭 수집**
- [ ] `prometheus-fastapi-instrumentator` 적용 (미들웨어 2줄, 자동 계측)
  - [ ] `/metrics` 엔드포인트 노출
  - [ ] 핵심 메트릭 대시보드 구성: 초당 요청수, P95 레이턴시, 4xx/5xx 에러율
- [ ] Prometheus docker-compose 서비스 추가 (포트 9090)

**로그 수집**
- [ ] Loki + Promtail docker-compose 서비스 추가
  - [ ] Promtail: Docker 소켓 마운트로 컨테이너 로그 자동 수집
  - [ ] 로그 보존 기간 설정

**시각화**
- [ ] Grafana docker-compose 서비스 추가 (포트 3000)
  - [ ] Prometheus + Loki 데이터소스 연결
  - [ ] FastAPI 기본 대시보드 구성
  - [ ] LLM 비용/토큰 대시보드 구성

**에러 트래킹**
- [ ] GlitchTip 도입 (Sentry SDK 호환, RAM 1-2GB)
  - [ ] `sentry-sdk[fastapi]` 설치 후 DSN만 GlitchTip으로 변경
  - [ ] 스택트레이스 + 릴리스 추적 설정
  - [ ] 기존 PostgreSQL과 연결 (별도 컨테이너 불필요)

**LLM 관찰성**
- [ ] Langfuse 도입 결정 (미결 — 셀프호스팅 vs 클라우드 무료 플랜)
  - [ ] `@observe()` 데코레이터로 AI 파이프라인 핸들러 계측
  - [ ] 토큰 사용량 / 비용 / 캐시 히트율 추적
  - [ ] Claude prompt caching 모니터링 (`cache_read_input_tokens` 필드)

**업타임 감시**
- [ ] Uptime Kuma docker-compose 서비스 추가 (포트 3001, SQLite 내장)
  - [ ] FastAPI `/health` 엔드포인트 등록
  - [ ] 알림 채널 연결 (Telegram + Discord)

### 알림 시스템 (Notification)

> 아키텍처: Strategy 패턴(채널 구현) + Observer/Event-driven(이벤트 분리)
> 원칙: 새 채널 추가 시 기존 코드 수정 없음 (OCP)

**공통 인터페이스 설계**
- [ ] `NotificationChannel` ABC 정의 (`async def send(recipient, message, **kwargs) -> bool`)
- [ ] `NotificationRegistry` 구현 (채널명 → 핸들러 동적 매핑)
- [ ] `EventBus` 구현 (Domain Event 발행/구독)
- [ ] 알림 전송을 `BackgroundTasks`로 API 응답과 분리

**Phase 1-A 구현 채널**
- [ ] **인앱 알림** (DB 저장 + 읽음 처리)
  - [ ] `notifications` 테이블 설계 (user_id, type, payload, read_at)
  - [ ] 알림 조회 API (`GET /notifications`, cursor 페이지네이션)
  - [ ] 알림 읽음 처리 API (`PATCH /notifications/:id/read`)
- [ ] **Telegram Bot** (에러/시스템 알림 — 개발자 전용)
  - [ ] BotFather에서 Bot Token 발급
  - [ ] `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` 환경변수 설정
  - [ ] `TelegramChannel` 구현 (`httpx` 비동기 호출)
  - [ ] 에러 발생 시 스택트레이스 요약 전송
- [ ] **Discord Webhook** (시스템 이벤트 알림 — 개발자 전용)
  - [ ] Discord 서버/채널 Webhook URL 발급
  - [ ] `DISCORD_WEBHOOK_URL` 환경변수 설정
  - [ ] `DiscordChannel` 구현 (embed 포맷, 색상 코드)
  - [ ] Webhook URL 환경변수로만 관리 (유출 시 누구나 발송 가능)

**Phase 1-B+ 확장 예정 채널**
- [ ] 이메일 (Resend — 3,000건/월 무료)
- [ ] Slack (개인 workspace Incoming Webhook)
- [ ] SMS (Twilio — 실 사용자 생기면)

**사용자 알림 이벤트 (Phase 1-A)**
- [ ] `NODE_CONFIRMED` — 노드 확정 시 인앱 알림
- [ ] `NODE_REJECTED` — 노드 거부 시 인앱 알림
- [ ] `PIPELINE_FAILED` — AI 파이프라인 실패 시 Telegram + Discord

### 운영 지표

- [ ] MSA 분리 트리거 모니터링 지표 설정
  - [ ] 단일 모듈 CPU 80%+ 지속 → 분리 검토
  - [ ] 모듈 간 호출 레이턴시 200ms+ 지속 → 분리 검토
- [ ] 비정상 접근 패턴 로깅 (반복 인증 실패, 대량 요청)
- [ ] LLM 비용 이상 급증 알림 (일일 예산 임계값 설정)
