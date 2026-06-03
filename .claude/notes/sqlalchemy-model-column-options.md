---
date: 2026-06-03
tags: [sqlalchemy, python, orm, model, enum, migration]
---

# SQLAlchemy mapped_column 옵션

## 핵심 개념
SQLAlchemy 2.0 스타일에서 `mapped_column()`에 사용하는 주요 옵션 정리.

## default vs server_default

| | default | server_default |
|--|---------|----------------|
| 실행 주체 | Python | DB |
| 사용 예 | UUID, 계산값 | 타임스탬프, DB 함수 |
| DB 스키마 | 스키마에 안 남음 | `DEFAULT NOW()` 스키마에 기록 |

```python
# default — Python이 INSERT 전에 값을 세팅
id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4)
is_public: Mapped[bool] = mapped_column(Boolean, default=False)

# server_default — DB가 INSERT 시점에 값을 세팅
created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

`created_at`에 `server_default=func.now()`를 쓰는 이유: DB 레벨에서 보장하면
Python 코드가 값을 빠뜨려도 항상 타임스탬프가 찍힌다.

`func.now()`는 SQLAlchemy 표현식 — SQL의 `NOW()` 함수 호출을 생성한다.

## Mapped[X | None] 과 nullable

```python
# nullable=False (기본값) — NOT NULL 제약
display_name: Mapped[str] = mapped_column(String, nullable=False)

# nullable=True — NULL 허용. Mapped 타입에도 | None 명시
deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
personal_space_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
```

`Mapped[X | None]`은 Python 타입 힌트, `nullable=True`는 DB 제약 — 둘 다 함께 써야 일관성이 유지된다.

## Enum 저장 방식 — 문자열 vs 숫자

### 숫자(ordinal) 저장 — 회피

```python
class OwnerType(enum.Enum):
    personal = 0
    group = 1
```

DB에 `0`, `1`로 저장 → 나중에 중간에 값을 추가하면 기존 데이터 의미가 바뀐다.

```python
# 나중에 이렇게 바뀌면
class OwnerType(enum.Enum):
    unknown = 0   # 추가
    personal = 1  # 밀림 — 기존 DB의 0이 unknown이 됨
    group = 2     # 밀림
```

### 문자열 저장 — 권장

```python
class OwnerType(str, enum.Enum):
    personal = "personal"  # DB에 "personal" 문자열로 저장
    group = "group"        # DB에 "group" 문자열로 저장
```

`str`을 같이 상속하면:
- DB에 문자열로 저장 → 순서 변경·중간 추가에 안전
- DB에서 직접 읽어도 의미가 명확
- JSON 직렬화 시 `"personal"` 문자열로 바로 변환

## Enum name 파라미터

```python
owner_type: Mapped[OwnerType] = mapped_column(Enum(OwnerType, name="owner_type"), nullable=False)
```

`name="owner_type"` — PostgreSQL에 생성될 ENUM 타입 이름을 명시한다.
생략하면 자동 생성된 이름이 붙어서 마이그레이션 충돌이 생길 수 있다.

## 관련 개념
- SQLAlchemy ORM, Alembic autogenerate, PostgreSQL ENUM 타입
