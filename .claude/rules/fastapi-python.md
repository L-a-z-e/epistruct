# FastAPI / Python 개발 규칙

> 이 파일은 알려진 에러 패턴의 트리거 역할을 한다.
> 아래 상황에 해당하면 연결된 knowledge 파일을 즉시 읽고 적용한다.

---

## 트리거 — 이 상황이 보이면 knowledge 파일을 먼저 읽어라

| 상황 | 읽어야 할 파일 |
|------|--------------|
| `config.py`에 `list[str]` / `list[int]` / `dict[*]` / `set[*]` 필드 추가 | `knowledge/errors/python/pydantic-settings-list-field.md` |
| `.env` / `.env.example`에 list 관련 환경변수 추가 | `knowledge/errors/python/pydantic-settings-list-field.md` |
| `pydantic_settings.exceptions.SettingsError` 에러 발생 | `knowledge/errors/python/pydantic-settings-list-field.md` |
| `model_dump()` 결과 dict에서 UUID 필드를 `uuid.UUID()` 로 감쌀 때 | `knowledge/errors/python/pydantic-model-dump-uuid.md` |
| `AttributeError: 'UUID' object has no attribute 'replace'` 발생 | `knowledge/errors/python/pydantic-model-dump-uuid.md` |
| Supabase webhook DELETE 이벤트 처리 시 | `knowledge/patterns/auth/supabase-webhook-payload.md` |

---

## BaseSettings 필드 선언 규칙

- 기본값 없는 필드(`database_url: str`) → .env에 반드시 존재해야 함. 없으면 시작 시 즉시 에러
- `list[*]` 타입 필드 → .env 값은 반드시 JSON 배열 형식: `["val1","val2"]`
- `bool` 타입 필드 → .env 값: `true` / `false` (소문자)

## 실행 환경 규칙

- 모든 Python 실행은 `uv run` 접두사 사용 — 가상환경 자동 적용
- `--reload` 플래그는 개발 환경에서만 — 운영 배포 시 제거

## SQLAlchemy async 규칙

- `expire_on_commit=False` 필수 — commit 후 객체 접근 시 의도치 않은 DB 재조회 방지
- `get_session()`은 `Depends()`로만 주입 — 직접 호출 금지
