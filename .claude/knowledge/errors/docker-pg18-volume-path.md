---
name: docker-pg18-volume-path
description: PostgreSQL 18 공식 이미지 볼륨 마운트 경로 변경 — /data 대신 / 사용
metadata:
  type: error
  severity: blocking
  stack: docker, postgresql
---

## 증상

`pgvector/pgvector:pg18` 이미지 기동 시 즉시 exit:

```
Error: there appears to be PostgreSQL data in /var/lib/postgresql/data (unused mount/volume)
In 18+, these Docker images are configured to store database data in a format
compatible with pg_ctlcluster (major-version-specific directory names).
```

## 원인

PostgreSQL 18부터 공식 Docker 이미지가 내부 디렉토리 구조를 변경.
- PG17 이하: `/var/lib/postgresql/data` 마운트
- PG18 이상: `/var/lib/postgresql` 마운트 (내부에서 `18/main/` 서브디렉토리 자동 생성)

## 해결

`docker-compose.yml` 볼륨 경로 수정:

```yaml
# 틀림 (PG17 이하 방식)
volumes:
  - postgres_data:/var/lib/postgresql/data

# 올바름 (PG18 이상)
volumes:
  - postgres_data:/var/lib/postgresql
```

기존 볼륨에 잘못된 데이터가 있으면 삭제 후 재기동:
```bash
docker compose down -v
docker compose up -d
```

## 예방

PG 메이저 버전 업그레이드 시 docker-library/postgres 릴리스 노트 확인.
참조: https://github.com/docker-library/postgres/pull/1259
