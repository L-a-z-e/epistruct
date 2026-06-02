# Epistruct 패키지 구조 설계

> 작성일: 2026-06-03
> 기반: DDD + Modular Monolith best practice 리서치 (5개 에이전트 병렬 조사)
> 참조 레포: benavlabs/FastAPI-boilerplate, arctikant/fastapi-modular-monolith-starter-kit, obytes/expo-starter

---

## 핵심 결정사항

### 1. 모듈 우선 수직 슬라이스 (Vertical Slice)

2024-2025 주류 패턴. 전역 레이어 분리(`app/api/`, `app/models/`) 대신,
도메인 모듈이 자체 레이어를 내부에 품는다.

```
modules/
└── knowledge/
    ├── domain/          ← 순수 비즈니스 규칙 (프레임워크 독립)
    ├── application/     ← 유스케이스 조율 (트랜잭션 경계)
    ├── infrastructure/  ← 구체 구현 (SQLAlchemy, 외부 API)
    └── presentation/    ← FastAPI 라우터 + Pydantic 스키마
```

### 2. 의존성 방향 (단방향)

```
Presentation → Application → Domain ← Infrastructure
```

- `Infrastructure`는 `Domain` 인터페이스를 구현하지만, `Domain`은 `Infrastructure`를 모른다.
- 모듈 간 직접 import 금지. `gateway.py` 또는 `__init__.py` 공개 API만 참조.

### 3. Repository 인터페이스 — Protocol 방식

`ABC` 대신 `Protocol` 사용. 테스트 Mock이 상속 없이 가능해 더 유연.

### 4. 도메인 모델 순수성 — Separate Model

ORM 모델(`infrastructure/models.py`)과 도메인 엔티티(`domain/entities.py`)를 분리.
Repository 내부에서 변환. 초기 복잡도는 높지만 ORM에 독립적.

### 5. 모듈 간 통신

| 케이스 | 방식 |
|--------|------|
| 동기 (다른 모듈 데이터 조회) | `gateway.py` 인터페이스 호출 |
| 비동기 (사이드 이펙트) | Domain Events → `fastapi-events` |
| 절대 금지 | 타 모듈 ORM 모델 직접 import, 타 모듈 DB 테이블 직접 JOIN |

---

## 백엔드 구조 (FastAPI)

```
epistruct-api/
├── pyproject.toml                  # uv 기반 의존성 관리
├── alembic.ini
├── .env                            # gitignore
├── .env.example
├── docker-compose.yml              # PostgreSQL + pgvector
│
├── migrations/
│   ├── env.py
│   └── versions/
│
├── src/
│   ├── main.py                     # FastAPI app factory, 라우터 등록
│   │
│   ├── core/                       # 공유 인프라 (모든 모듈이 의존 가능)
│   │   ├── config.py               # Pydantic Settings (env 읽기)
│   │   ├── database.py             # async engine, AsyncSession factory
│   │   ├── dependencies.py         # get_session, get_current_user 공통 dep
│   │   ├── exceptions.py           # 공통 예외 클래스 + 핸들러
│   │   ├── security.py             # Supabase JWKS JWT 검증
│   │   └── events.py               # in-process 이벤트 버스
│   │
│   ├── shared/                     # 모듈 간 공유 Value Objects (최소화 원칙)
│   │   └── types.py                # EntityId 등 범용 Value Object
│   │
│   └── modules/
│       │
│       ├── auth/                   # JWT 검증 + users 프로필 모듈
│       │   ├── __init__.py         # 공개 API만 export (gateway, schemas, deps)
│       │   ├── gateway.py          # 타 모듈용 facade (IAuthGateway + impl)
│       │   ├── domain/
│       │   │   ├── entities.py     # User (도메인 엔티티, ORM 독립)
│       │   │   ├── repositories.py # IUserRepository (Protocol)
│       │   │   └── events.py       # UserCreated, UserDeleted
│       │   ├── application/
│       │   │   ├── services.py     # UserService (프로필 조회/수정 유스케이스)
│       │   │   └── unit_of_work.py
│       │   ├── infrastructure/
│       │   │   ├── models.py       # SQLAlchemy ORM UserModel
│       │   │   ├── repositories.py # UserRepository 구현체
│       │   │   └── webhook.py      # Supabase webhook → users 자동 생성
│       │   └── presentation/
│       │       ├── router.py       # /api/v1/users, /internal/webhook
│       │       ├── schemas.py      # UserResponse, UpdateProfileRequest
│       │       └── dependencies.py # CurrentUser, ActiveUser dep
│       │
│       ├── knowledge/              # 노드 + 관계 + 그래프 (핵심 도메인)
│       │   ├── __init__.py
│       │   ├── gateway.py          # IKnowledgeGateway (space 모듈이 사용)
│       │   ├── domain/
│       │   │   ├── entities.py     # Node, NodeRelationship
│       │   │   ├── value_objects.py # NodeType(P/C/M/D), RelationshipType(6종)
│       │   │   ├── repositories.py # INodeRepository, IRelationshipRepository
│       │   │   └── events.py       # NodeConfirmed, NodeRejected, NodeUpdated
│       │   ├── application/
│       │   │   ├── services.py     # NodeService (CRUD, 그래프 조회, 확정/거부)
│       │   │   └── unit_of_work.py
│       │   ├── infrastructure/
│       │   │   ├── models.py       # NodeModel, NodeRelationshipModel
│       │   │   └── repositories.py
│       │   └── presentation/
│       │       ├── router.py       # /api/v1/nodes, /api/v1/graph
│       │       ├── schemas.py
│       │       └── dependencies.py
│       │
│       ├── space/                  # 공간 + 멤버십 모듈
│       │   ├── __init__.py
│       │   ├── gateway.py
│       │   ├── domain/
│       │   │   ├── entities.py     # Space, Group, GroupMember
│       │   │   ├── value_objects.py # SpaceType(personal/group), Role(4종)
│       │   │   ├── repositories.py
│       │   │   └── events.py       # SpaceCreated, MemberAdded
│       │   ├── application/
│       │   │   ├── services.py     # SpaceService, GroupService
│       │   │   └── unit_of_work.py
│       │   ├── infrastructure/
│       │   │   ├── models.py       # SpaceModel, GroupModel, GroupMemberModel
│       │   │   └── repositories.py
│       │   └── presentation/
│       │       ├── router.py       # /api/v1/spaces, /api/v1/groups
│       │       ├── schemas.py
│       │       └── dependencies.py # SpaceAccessChecker dep
│       │
│       └── ai_pipeline/            # LLM + 임베딩 + 추출 모듈
│           ├── __init__.py
│           ├── domain/
│           │   ├── entities.py     # Source, Chunk, ExtractionJob
│           │   ├── value_objects.py # SourceType(url/pdf/youtube/text/conv)
│           │   └── repositories.py # ISourceRepository, IChunkRepository
│           ├── application/
│           │   ├── services.py     # PipelineService (Source 처리 진입점)
│           │   ├── jobs.py         # BackgroundTask 비동기 작업 정의
│           │   └── unit_of_work.py
│           ├── infrastructure/
│           │   ├── models.py       # SourceModel, ChunkModel
│           │   ├── repositories.py
│           │   ├── llm/
│           │   │   ├── client.py   # Claude API 클라이언트
│           │   │   └── schemas.py  # LLM structured output JSON schema
│           │   └── extractors/     # Source 타입별 텍스트 추출
│           │       ├── url.py      # httpx 크롤링
│           │       ├── pdf.py      # PyMuPDF
│           │       └── youtube.py  # yt-dlp 자막
│           └── presentation/
│               ├── router.py       # /api/v1/pipeline/sources
│               └── schemas.py
│
└── tests/
    ├── unit/
    │   └── modules/                # src/modules 구조 미러링
    ├── integration/                # 실제 DB 연결 테스트
    └── architecture/
        └── test_boundaries.py      # 모듈 간 직접 import 위반 감지
```

---

## 프론트엔드 구조 (Expo)

```
epistruct-app/
├── package.json
├── tsconfig.json                   # @/ 절대경로 alias 설정
├── app.json
│
├── app/                            # Expo Router — 라우팅만, 로직 없음
│   ├── _layout.tsx                 # Root layout (providers 등록)
│   ├── (auth)/                     # 비인증 라우트 그룹
│   │   ├── _layout.tsx
│   │   ├── login.tsx               # export { LoginScreen as default } from '@/features/auth'
│   │   └── signup.tsx
│   └── (app)/                      # 인증 라우트 그룹
│       ├── _layout.tsx             # Tab navigator
│       ├── index.tsx               # → features/knowledge-graph
│       ├── input.tsx               # → features/source-input
│       ├── review.tsx              # → features/node-review
│       └── node/
│           └── [id].tsx            # → features/node-editor
│
└── src/
    ├── features/                   # 기능 모듈 (자체 완결)
    │   │
    │   ├── auth/                   # F0: 인증
    │   │   ├── login-screen.tsx
    │   │   ├── signup-screen.tsx
    │   │   ├── use-auth-store.tsx
    │   │   └── components/
    │   │       ├── login-form.tsx
    │   │       └── social-login-button.tsx
    │   │
    │   ├── source-input/           # F1: 혼합 입력 (URL/PDF/YouTube/텍스트)
    │   │   ├── source-input-screen.tsx
    │   │   ├── api.ts              # POST /pipeline/sources
    │   │   ├── use-source-input-store.tsx
    │   │   └── components/
    │   │       ├── url-input-tab.tsx
    │   │       ├── pdf-picker-tab.tsx
    │   │       ├── youtube-input-tab.tsx
    │   │       └── text-input-tab.tsx
    │   │
    │   ├── node-review/            # F2: draft 노드 확정/거부
    │   │   ├── node-review-screen.tsx
    │   │   ├── api.ts              # GET /nodes?status=draft, PATCH /nodes/:id/confirm
    │   │   ├── use-node-review-store.tsx
    │   │   └── components/
    │   │       ├── draft-node-card.tsx
    │   │       ├── node-type-badge.tsx
    │   │       └── review-action-bar.tsx
    │   │
    │   ├── knowledge-graph/        # F3: 그래프 시각화
    │   │   ├── knowledge-graph-screen.tsx
    │   │   ├── api.ts              # GET /graph
    │   │   ├── use-graph-store.tsx
    │   │   └── components/
    │   │       ├── graph-canvas.web.tsx    # 웹: react-force-graph
    │   │       └── graph-list.tsx          # 네이티브: 리스트/트리 대체
    │   │
    │   └── node-editor/            # F4: 노드 편집/병합/삭제
    │       ├── node-editor-screen.tsx
    │       ├── api.ts              # PATCH /nodes/:id, DELETE /nodes/:id
    │       ├── use-node-editor-store.tsx
    │       └── components/
    │           ├── node-detail-form.tsx
    │           └── relationship-list.tsx
    │
    ├── components/ui/              # 2개 이상 feature에서 쓰는 공유 UI 원시요소
    │   ├── button.tsx
    │   ├── input.tsx
    │   ├── card.tsx
    │   ├── badge.tsx
    │   ├── modal.tsx
    │   └── icons/
    │
    └── lib/                        # feature가 의존하는 공유 인프라
        ├── api/
        │   ├── client.ts           # axios 인스턴스 (baseURL, 인터셉터)
        │   └── types.ts            # Envelope 타입 (ApiResponse<T>, ApiError)
        ├── auth/
        │   ├── supabase.ts         # Supabase client 초기화
        │   └── hooks.ts            # useSession, useCurrentUser
        ├── hooks/
        │   ├── use-debounce.ts
        │   └── use-app-state.ts
        └── types/
            └── index.ts            # 공유 도메인 타입 (NodeType, RelationshipType)
```

---

## 모듈 간 통신 패턴 예시

### Gateway 패턴 (동기 조회)

```python
# auth/gateway.py
from typing import Protocol
from .application.services import UserService
from .domain.entities import UserDTO

class IAuthGateway(Protocol):
    async def get_user_dto(self, user_id: str) -> UserDTO: ...

class AuthGateway:
    def __init__(self, user_service: UserService):
        self._service = user_service

    async def get_user_dto(self, user_id: str) -> UserDTO:
        return await self._service.get_user_dto(user_id)

# auth/__init__.py
from .gateway import IAuthGateway, AuthGateway
from .presentation.dependencies import CurrentUser, ActiveUser

__all__ = ["IAuthGateway", "AuthGateway", "CurrentUser", "ActiveUser"]
# UserModel, UserService 등 내부 구현은 __all__ 미포함 → 외부 접근 차단
```

### 이벤트 기반 (비동기 사이드 이펙트)

```python
# auth/domain/events.py
from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class UserCreated:
    user_id: str
    email: str
    occurred_at: datetime

# space/listeners.py — auth를 직접 import하지 않음
from fastapi_events.handlers.local import local_handler
from fastapi_events.typing import Event

@local_handler.register(event_name="UserCreated")
async def on_user_created(event: Event):
    # 가입 시 개인 공간 자동 생성
    await space_service.create_personal_space(user_id=event[1]["user_id"])
```

---

## 모듈 경계 강제

### 아키텍처 테스트 (tests/architecture/test_boundaries.py)

```python
import ast
import pathlib
import pytest

@pytest.mark.parametrize("module", ["auth", "knowledge", "space", "ai_pipeline"])
def test_module_does_not_import_other_internals(module):
    for py_file in pathlib.Path(f"src/modules/{module}").rglob("*.py"):
        if py_file.name == "__init__.py":
            continue
        tree = ast.parse(py_file.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for other in ["auth", "knowledge", "space", "ai_pipeline"]:
                    if other == module:
                        continue
                    # 내부 경로 직접 접근 금지 (공개 __init__ 경유만 허용)
                    if node.module.startswith(f"src.modules.{other}."):
                        pytest.fail(
                            f"{py_file}: '{other}' 내부를 직접 import. "
                            f"'{other}.__init__' 공개 API만 사용할 것."
                        )
```

---

## 네이밍 규칙 요약

### 백엔드 (Python)

| 파일 종류 | 이름 패턴 | 예시 |
|----------|----------|------|
| 도메인 엔티티 | `entities.py` | `class Node:` |
| Value Object | `value_objects.py` | `class NodeType(str, Enum):` |
| Repository 인터페이스 | `repositories.py` | `class INodeRepository(Protocol):` |
| ORM 모델 | `models.py` | `class NodeModel(Base):` |
| 유스케이스 서비스 | `services.py` | `class NodeService:` |
| FastAPI 라우터 | `router.py` | `router = APIRouter(prefix="/nodes")` |
| Pydantic 스키마 | `schemas.py` | `class NodeResponse(BaseModel):` |
| FastAPI 의존성 | `dependencies.py` | `async def get_node_service(...)` |

### 프론트엔드 (TypeScript)

| 파일 종류 | 이름 패턴 | 예시 |
|----------|----------|------|
| 스크린 컴포넌트 | `{feature}-screen.tsx` | `node-review-screen.tsx` |
| API 호출 | `api.ts` (feature 내 단일) | `export const confirmNode = ...` |
| 상태 관리 | `use-{feature}-store.tsx` | `use-node-review-store.tsx` |
| 공유 UI | `{component}.tsx` (kebab) | `draft-node-card.tsx` |
| 플랫폼 분기 | `{name}.web.tsx` / `{name}.tsx` | `graph-canvas.web.tsx` |

> **Expo 주의**: `features/` 하위에 `index.ts` barrel export 금지.
> Expo Fast Refresh가 barrel 파일을 잘못 처리해 hot reload 오류 발생.

---

## 참고 레포지토리

| 레포 | Stars | 참고 포인트 |
|------|-------|------------|
| [benavlabs/FastAPI-boilerplate](https://github.com/benavlabs/FastAPI-boilerplate) | 1.9k | uv workspace, modules/ 수직 슬라이스, async |
| [arctikant/fastapi-modular-monolith-starter-kit](https://github.com/arctikant/fastapi-modular-monolith-starter-kit) | 47 | gateway.py + 이벤트 패턴 교과서 |
| [teamhide/fastapi-boilerplate](https://github.com/teamhide/fastapi-boilerplate) | 1.5k | @Transactional 데코레이터, Event Dispatcher |
| [obytes/expo-starter](https://starter.obytes.com) | — | app/ 라우팅 분리, features/ 자체 완결 |
