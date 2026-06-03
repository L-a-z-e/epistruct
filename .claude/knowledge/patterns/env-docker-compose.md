---
name: env-docker-compose
description: docker-compose에서 .env 참조 패턴 — 기본값 없이 엄격하게 관리
metadata:
  type: pattern
  stack: docker, security
---

## 패턴

docker-compose.yml에서 환경변수를 `.env`에서만 읽고 **기본값을 두지 않는다**.

```yaml
# 틀림 — 기본값이 있으면 .env 없어도 기동됨 (실수 유발)
environment:
  POSTGRES_USER: ${POSTGRES_USER:-epistruct}
  POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-epistruct}

# 올바름 — .env 없으면 기동 불가 → 실수 방지
environment:
  POSTGRES_USER: ${POSTGRES_USER}
  POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
```

## .env.example 규칙

- 실제값 없이 플레이스홀더만 작성
- `DATABASE_URL`은 구성 방법을 보여주는 형태로

```bash
POSTGRES_USER=your-db-user
POSTGRES_PASSWORD=your-db-password
POSTGRES_DB=your-db-name
DATABASE_URL=postgresql+asyncpg://your-db-user:your-db-password@localhost:5432/your-db-name
```

## .gitignore 필수 항목

```
.env
.env.local
.env.*.local
```

## 이유

기본값이 있으면 `.env`를 만들지 않아도 서비스가 기동되어 실제 자격증명 없이
개발 환경이 돌아가는 착각을 유발함. 엄격한 강제가 초기 셋업 비용을 줄임.
