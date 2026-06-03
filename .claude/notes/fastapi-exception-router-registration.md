---
date: 2026-06-03
tags: [fastapi, exception-handler, include-router, spring]
---

# FastAPI 예외 처리 등록 & 라우터 등록 패턴

## 핵심 개념
FastAPI는 Spring과 달리 자동 컴포넌트 스캔이 없다. 예외 핸들러와 라우터 모두 main.py에서 명시적으로 등록해야 한다.

---

## register_exception_handlers — Spring @ControllerAdvice와 동일

```python
# src/core/exceptions.py
def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={...})
```

Spring 비유:
```java
@RestControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(AppException.class)
    public ResponseEntity<?> handleAppException(AppException e) { ... }
}
```

**차이점**: Spring은 `@RestControllerAdvice` 빈을 컨테이너가 자동 탐색·등록하지만,
FastAPI는 자동 탐색이 없어서 `main.py`에서 `register_exception_handlers(app)` 직접 호출 필요.

---

## include_router — 라우터 명시적 등록

```python
# main.py
app.include_router(core_router)                          # prefix 없음 (/health 등)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(knowledge_router, prefix="/api/v1")
```

Spring 비교:
```java
// Spring — @RestController 붙이면 컴포넌트 스캔으로 자동 등록
@RestController
@RequestMapping("/api/v1/auth")
public class AuthController { ... }
```

**FastAPI 명시적 등록의 장점**: 앱에 붙어있는 라우터 전체가 main.py 한 곳에서 보인다.

---

## health router 분리 패턴

인라인으로 main.py에 두지 않고 `src/core/router.py`로 분리:

```python
# src/core/router.py
router = APIRouter()

@router.get("/health")
async def health():
    async with AsyncSessionFactory() as session:
        await session.execute(text("SELECT 1"))  # DB ping 포함
    return {"status": "ok"}
```

main.py에서 `prefix` 없이 등록 → `/health` 로 접근 가능.

---

## 관련 개념
- `prefix="/api/v1"` — include_router 시 URL prefix 일괄 적용
- Middleware → 라우터보다 앞단 공통 처리 (`fastapi-middleware.md` 참조)
