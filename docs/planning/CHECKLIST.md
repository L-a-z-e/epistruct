# Epistruct 개발 체크리스트

> 마지막 업데이트: 2026-06-01
> 기준 문서: [PRD v0.7](../prd/Epistruct_PRD_v0.7.md)

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
- [ ] ERD 작성
  - [ ] `users` 테이블
  - [ ] `spaces` + `space_members` 테이블 (personal 구현, group 껍데기)
  - [ ] `sources` 테이블 (url/pdf/youtube/text/conversation)
  - [ ] `chunks` 테이블 (embedding vector 예약)
  - [ ] `nodes` 테이블 (label/display_name/embedding 예약)
  - [ ] `node_relationships` 테이블 (6종 관계)
  - [ ] `node_sources` 브릿지 테이블
  - [ ] `node_lineage` 테이블 (껍데기)
  - [ ] `node_proposals` 테이블 (껍데기)
- [ ] API 명세 초안
  - [ ] auth 모듈 (JWT 검증 미들웨어, users 프로필, Supabase webhook)
  - [ ] knowledge 모듈 (nodes CRUD, relationships, graph 조회)
  - [ ] space 모듈 (spaces CRUD, space_members)
  - [ ] ai_pipeline 모듈 (source 처리, 노드 추출, 임베딩)
- [ ] 노드 추출 리뷰 UX 플로우 (draft → confirmed/rejected)
- [ ] 노드 추출 LLM structured output 스키마 정의

### 백엔드 구현 (FastAPI)
- [ ] 프로젝트 셋업 (Modular Monolith 구조)
- [ ] PostgreSQL + pgvector 연결
- [ ] Supabase Auth 연동 (JWT 검증 미들웨어)
- [ ] Supabase webhook → users 테이블 자동 생성
- [ ] F0: 인증 엔드포인트 (프로필 조회/수정)
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

## 인프라 / 운영

- [ ] 개발 환경 셋업 (docker-compose: PostgreSQL + pgvector)
- [ ] CI/CD 파이프라인 구성
- [ ] 스테이징 환경 구성
- [ ] 모니터링 (에러, LLM 비용, 응답 지연)
- [ ] MSA 분리 트리거 모니터링 지표 설정
