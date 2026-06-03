# Runtime Versions

> 확정일: 2026-06-03
> 원칙: LTS 우선, 버전 변경은 단일 파일 수정으로 완결

---

## 확정 버전

| 런타임 | 버전 | EOL | 고정 파일 |
|--------|------|-----|----------|
| Python | **3.12** | 2028-10-31 | `.python-version` |
| Node.js | **24 LTS** | 2028-04-30 | `.nvmrc` |
| PostgreSQL | **18** | 2030-11-14 | `docker-compose.yml` 이미지 태그 |
| pgvector | **0.8.2** | - | `docker-compose.yml` 이미지 태그 |
| Expo SDK | **53** | - | `package.json` |

---

## 버전 관리 구조 (Java SDKMAN! 대응)

| Java | Python | Node.js |
|------|--------|---------|
| SDKMAN! | `uv` | `nvm` |
| `.sdkmanrc` | `.python-version` | `.nvmrc` |
| `sdk env install` | `uv python install 3.12` | `nvm install` |
| `sdk use java 21` | `uv python pin 3.12` | `nvm use` |

---

## 버전 고정 파일 규칙

### Python — `.python-version`
```
3.12
```
- `uv`가 자동으로 읽음. `pyenv`도 동일한 파일 포맷 사용.
- `pyproject.toml`의 `requires-python`과 반드시 일치시킨다.

```toml
# pyproject.toml
[project]
requires-python = ">=3.12,<3.13"
```

### Node.js — `.nvmrc`
```
24
```
- `nvm use` 또는 `nvm install` 실행 시 자동으로 읽음.
- `package.json`의 `engines`와 반드시 일치시킨다.

```json
// package.json (모노레포 루트)
{
  "engines": {
    "node": ">=24"
  }
}
```

### PostgreSQL — `docker-compose.yml`
```yaml
services:
  db:
    image: pgvector/pgvector:pg18
```

---

## 버전 변경 절차

### Python 버전 업그레이드 (예: 3.12 → 3.13)

```bash
# 1. Python 설치
uv python install 3.13

# 2. 버전 고정 파일 변경 (Java의 .sdkmanrc 수정과 동일)
uv python pin 3.13            # .python-version → "3.13"

# 3. pyproject.toml 업데이트
# requires-python = ">=3.13,<3.14"

# 4. 가상환경 재구성
uv sync

# 5. 의존성 호환성 확인 후 CI 통과 확인
```

### Node.js 버전 업그레이드 (예: 24 → 26)

```bash
# 1. Node.js 설치
nvm install 26

# 2. 버전 고정 파일 변경
echo "26" > .nvmrc

# 3. 전환 및 의존성 재설치
nvm use
pnpm install

# 4. package.json engines 필드 업데이트
# "node": ">=26"
```

### PostgreSQL 버전 업그레이드 (예: 18 → 19)

```bash
# 1. docker-compose.yml 이미지 태그 변경
# image: pgvector/pgvector:pg19

# 2. 기존 볼륨 백업 (데이터 영속화 볼륨)
docker compose exec db pg_dumpall -U postgres > backup.sql

# 3. 기존 컨테이너·볼륨 삭제 후 새 버전 기동
docker compose down -v
docker compose up -d

# 4. 백업 복원
docker compose exec -T db psql -U postgres < backup.sql
```

---

## 업그레이드 타이밍 기준

- **EOL 6개월 전** 업그레이드 계획 수립
- **EOL 3개월 전** 스테이징 환경에서 새 버전 검증 완료
- **EOL 1개월 전** 프로덕션 전환

| 버전 | EOL | 업그레이드 시작 목표 |
|------|-----|-------------------|
| Python 3.12 | 2028-10-31 | 2028-04 |
| Node.js 24 | 2028-04-30 | 2027-10 |
| PostgreSQL 18 | 2030-11-14 | 2030-05 |
