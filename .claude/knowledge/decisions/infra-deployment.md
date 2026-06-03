# 배포 아키텍처 결정

> 확정일: 2026-06-03
> 관련 리서치: 대화 기록 (AWS 프리티어 분석, Langfuse 셀프호스팅 리소스 분석)

---

## 핵심 결정

| 항목 | 결정 | 이유 |
|------|------|------|
| 배포 플랫폼 | **AWS ECS Fargate** | 서비스별 독립 Task, 사용량 기반 과금, Modular Monolith → MSA 전환 경로 자연스러움 |
| 개발 환경 | **로컬 Docker Compose 전용** | 배포 단계와 완전 분리 |
| DB | **RDS PostgreSQL 18** (배포) | 관리형 백업/failover, pgvector 지원 확인됨 |
| 모니터링 | **ECS 별도 Task** | EC2 t2.micro(1GB RAM)에서 Prometheus+Grafana 실행 불가 → Fargate로 독립 |
| LLM 관찰성 | **Langfuse 클라우드 무료 플랜** (Phase 1-A) | 셀프호스팅 최소 스펙 4vCPU/16GB — 현 단계 과잉. 50,000 이벤트/월 무료로 충분 |
| AWS 계정 | 2025년 7월 15일 이후 가입 | 크레딧 기반 ($100~$200, 6개월) — 12개월 프리티어 없음 |

---

## ECS Fargate 선택 근거

**왜 EC2가 아닌가**
- EC2 t2.micro (1GB): FastAPI + PostgreSQL만으로 메모리 빠듯. Prometheus+Grafana 추가 불가
- 모니터링을 별도 인스턴스에 올리면 비용이 선형 증가
- 인스턴스 관리(패치, 재시작) 부담

**왜 EKS가 아닌가**
- 개인 프로젝트 수준에서 오버엔지니어링
- 초기 설정 복잡도 너무 높음 (학습 목적이 분산될 수 있음)
- ECS Fargate로 충분한 서비스 분리 달성 가능

**ECS Fargate 장점**
- 서비스별 독립 Task Definition → 모니터링 / 앱 / DB 완전 분리
- 사용한 만큼만 과금 (vCPU 시간 + 메모리 시간)
- 껐다켜기 용이 (Task 0으로 설정하면 비용 0)
- `docker-compose.yml` → ECS Task Definition 변환 경로 존재
- Modular Monolith 모듈 → 나중에 별도 ECS Service로 뽑기 용이

---

## 서비스 아키텍처

```
[Expo Client]
    ↓ HTTPS
[ALB - Application Load Balancer]
    ↓
[ECS Fargate Cluster]
├── epistruct-api       (FastAPI — auth/knowledge/space/ai_pipeline 모듈)
├── epistruct-worker    (비동기: 임베딩 생성, AI 파이프라인)
└── monitoring          (Prometheus + Grafana + Loki + GlitchTip)

[RDS PostgreSQL 18 + pgvector 0.8.2]
[ElastiCache Redis]     (Rate limiting, 캐시 — Phase 1-A 또는 B)
```

---

## 환경별 전략

### 개발 환경 (현재)
- **로컬 Docker Compose만 사용** — AWS 배포 없음
- RAM 128GB로 풀스택 모니터링 포함 전체 실행 가능
- `docker-compose.yml` 서비스 정의가 ECS Task Definition의 기반

```yaml
# docker-compose.yml 서비스 목록 (기준)
services:
  api:          # → ECS Service: epistruct-api
  worker:       # → ECS Service: epistruct-worker
  db:           # → RDS로 대체 (배포 시 제거)
  prometheus:   # → ECS Service: monitoring
  grafana:      # → ECS Service: monitoring
  loki:         # → ECS Service: monitoring
  promtail:     # → ECS Service: monitoring
  glitchtip:    # → ECS Service: error-tracking
  uptime-kuma:  # → ECS Service: uptime
  redis:        # → ElastiCache로 대체 (배포 시)
```

### 배포 환경 (MVP 착수 시)
- ECS Fargate + RDS PostgreSQL 18
- Task별 CPU/메모리 설정으로 서비스별 독립 스케일링
- ALB로 HTTPS 종료 및 라우팅
- 실 사용자 없는 동안: Task desiredCount=0으로 비용 0 운영 가능

### MSA 전환 시 (트리거 조건 도달 시)
- Modular Monolith 모듈 경계 → 별도 ECS Service로 분리
- `ai_pipeline` 모듈: LLM 비용 30% 초과 시 우선 분리 대상
- `knowledge` 모듈: DAU 10,000 초과 시

---

## AWS 비용 주의사항

**숨겨진 비용 4대 지뢰 (실제 $43 청구 사례)**

| 항목 | 회피 방법 |
|------|---------|
| NAT 게이트웨이 (~$33/월) | 퍼블릭 서브넷 직접 사용 (개발 단계) |
| 미연결 탄력적 IP | Task 중지 시 IP도 해제 |
| CloudWatch 로그 무한 보존 | 30일 보존 정책 명시적 설정 |
| RDS gp3 스토리지 선택 | gp2 선택 (무료 한도 있음) |

**ECS Fargate 비용 예시 (us-east-1)**
- vCPU: $0.04048/시간
- 메모리: $0.004445/GB/시간
- 실 사용자 없는 개발 단계: desiredCount=0 → 과금 없음
- 크레딧 $100: 약 1-2개월 테스트 배포 운영 가능 수준

---

## Langfuse 결정 상세

**Phase 1-A: 클라우드 무료 플랜**
- 50,000 이벤트/월 무료
- 설정: `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` 환경변수만
- `@observe()` 데코레이터로 AI 파이프라인 계측

**Phase 2+ 재검토 조건**
- 월 50,000 이벤트 초과 시
- 또는 데이터 프라이버시 요구사항 강화 시
- 셀프호스팅 최소 스펙: 4vCPU + 16GB RAM (t3.xlarge, ~$150+/월)

---

## 미결 사항

- [ ] RDS PostgreSQL 18에서 pgvector 0.8.2 Extension 지원 확인 필요
- [ ] ECS Task Definition 초안 작성 (배포 착수 시)
- [ ] ALB HTTPS 인증서 (ACM) 설정
- [ ] ElastiCache Redis 도입 시점 결정 (Rate limiting 필요 시)
