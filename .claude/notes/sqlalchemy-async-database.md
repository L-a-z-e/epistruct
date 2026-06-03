---
date: 2026-06-03
tags: [python, sqlalchemy, asyncpg, database, fastapi, spring]
---

# SQLAlchemy 비동기 DB 연결

## 핵심 개념
SQLAlchemy async engine + sessionmaker + Base + get_session yield 패턴으로 FastAPI 비동기 DB 연결을 구성한다.

---

## 1. create_async_engine — DB 연결 풀 (Spring DataSource)

```python
engine = create_async_engine(
    settings.database_url,                    # postgresql+asyncpg://user:pw@host/db
    echo=settings.app_env == "development"    # 개발 환경에서 SQL 쿼리 콘솔 출력
)
```

Spring의 `DataSource` 빈과 동일. URL에 `asyncpg`가 붙는 이유는 비동기 드라이버 지정.

```
postgresql+asyncpg://epistruct:epistruct@localhost:5432/epistruct
           ^^^^^^^^
           비동기 드라이버 지정 (동기: psycopg2)
```

---

## 2. async_sessionmaker — 세션 팩토리 (Spring EntityManagerFactory)

```python
AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False)
```

`expire_on_commit=False` 이유: 기본값 True이면 commit 후 객체 속성 접근 시 DB 재조회 발생.
비동기 환경에서 예상치 못한 쿼리를 유발하므로 False로 설정.

---

## 3. Base — ORM 모델 부모 클래스 (Spring @Entity 등록 기반)

```python
class Base(DeclarativeBase):
    pass
```

모든 SQLAlchemy 모델이 이 클래스를 상속한다.

```python
# repositories/models.py 에서
class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True)
```

---

## 4. get_session — 요청마다 세션 주입 (yield 패턴)

```python
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionFactory() as session:
        yield session
        # 함수 종료 시 세션 자동 닫힘 + 예외 시 rollback
```

FastAPI Depends()와 연결:

```python
@router.get("/spaces")
async def list_spaces(session: AsyncSession = Depends(get_session)):
    # session 자동 주입
    # 함수 끝나면 get_session yield 뒤 실행 → 세션 닫힘
    ...
```

Spring `@Transactional` + `EntityManager` 주입과 유사. 트랜잭션 범위 = 요청 1개당 세션 1개.

---

## 관련 개념
- `AsyncGenerator[AsyncSession, None]` — yield를 쓰는 함수의 반환 타입 힌트
- `asyncpg` — PostgreSQL 비동기 드라이버 (동기 버전: psycopg2)
- `Depends(get_session)` — FastAPI 의존성 주입. 라우터 파라미터에 자동 주입
- `python-async-syntax-basics.md` — yield, async with 패턴 기초
