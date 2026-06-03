---
date: 2026-06-03
tags: [alembic, uv, python, sqlalchemy, migration]
---

# Alembic 설정 과정에서 학습한 개념들

## 핵심 개념
Alembic(DB 마이그레이션 도구) 설정 과정에서 나온 uv, ini 파일, env.py 구조, Python 기초 개념 정리.

## uv vs npm 비교

| npm | uv |
|-----|----|
| `npm install pgvector` | `uv add pgvector` |
| `package.json` + `package-lock.json` | `pyproject.toml` + `uv.lock` |
| `npm install` (lock 기준 설치) | `uv sync` |

- `uv add pgvector` = pyproject.toml에 추가 + 설치를 한 번에
- pyproject.toml 직접 편집 후 `uv sync`도 동일한 결과

## Alembic vs Flyway 비교

둘 다 "DB 스키마 변경을 코드로 버전 관리"하는 도구.

| | Flyway | Alembic |
|--|--------|---------|
| 언어 생태계 | Java/Kotlin | Python (SQLAlchemy 연동) |
| 마이그레이션 작성 | SQL 파일 직접 작성 | Python 코드 or SQL |
| **autogenerate** | 없음 — 직접 작성 | **있음** — 모델 보고 자동 생성 |
| 버전 관리 | 파일명 순서 (`V1__`, `V2__`) | 해시 기반 체인 |

핵심 차이: **autogenerate** — SQLAlchemy 모델(`models.py`)을 작성하면 Alembic이 현재 DB 상태와 비교해서 `ALTER TABLE`, `CREATE TABLE` SQL을 자동으로 만들어줌.

## .ini 파일 형식

설정값을 `키 = 값` 형태로 저장하는 텍스트 파일 형식. Python 표준 라이브러리 `configparser`가 읽는 포맷. 섹션(`[alembic]`, `[loggers]`)으로 구분.

```ini
[alembic]
script_location = %(here)s/alembic
sqlalchemy.url =
```

## %(here)s 문법

`configparser`의 변수 보간(interpolation) 문법.

```
%(변수명)s
```

- `here` = 이 `.ini` 파일이 위치한 디렉토리 절대경로 (내장 변수)
- Python의 `__file__`의 디렉토리 버전
- 파일을 어디서 실행해도 경로가 깨지지 않게 하려고 사용
- 끝의 `s` = Python `%` 포맷팅의 문자열 타입 지정자

## env.py 구조

마이그레이션 실행 시 Alembic이 이 파일을 진입점으로 사용.

### 핵심 설정

```python
config.set_main_option("sqlalchemy.url", settings.database_url)
target_metadata = Base.metadata
```

- `settings.database_url` → `.env`의 DB URL을 Alembic에 주입
- `Base.metadata` → SQLAlchemy 모델 정보를 Alembic에 연결 (autogenerate 기반)

### offline vs online 모드

- `offline` — DB 없이 SQL 파일만 출력. CI나 DBA에게 SQL 전달할 때 사용
- `online` — 실제 DB에 직접 연결해서 실행. 일반적으로 쓰는 모드

### async 브리지 패턴

Alembic 자체는 동기(sync) 설계. asyncpg(비동기 드라이버)를 쓰기 때문에 브리지 필요:

```python
async def run_async_migrations() -> None:
    connectable = async_engine_from_config(...)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)  # async → sync 브리지
```

async 엔진으로 연결 → `run_sync()`로 Alembic 마이그레이션 실행.

## Python 기초 개념

### None 타입

Python의 "값 없음"을 나타내는 특수 값. 타입은 `NoneType`.
Java의 `null`, JavaScript의 `null`과 같은 개념.

```python
target_metadata = None           # 아직 아무것도 없다
target_metadata = Base.metadata  # 실제 값으로 교체
```

### 키워드 인자 (keyword argument)

```python
context.configure(connection=connection, target_metadata=target_metadata)
```

- 왼쪽 = 파라미터 이름, 오른쪽 = 전달할 변수
- 이름이 우연히 같을 뿐 (`connection=connection`)
- 순서 상관없이 이름으로 전달 가능, 가독성 향상

### set_main_option 문자열 키

```python
config.set_main_option("sqlalchemy.url", settings.database_url)
```

`alembic.ini`의 `[alembic]` 섹션을 딕셔너리처럼 다루는 메서드.
파일에 DB 비밀번호를 하드코딩하지 않고 런타임에 덮어쓰는 패턴.

## 관련 개념
- SQLAlchemy ORM, asyncpg, pydantic-settings, pyproject.toml
