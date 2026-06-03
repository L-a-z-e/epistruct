---
date: 2026-06-03
tags: [fastapi, middleware, cors, spring]
---

# FastAPI Middleware

## 핵심 개념
요청이 라우터에 도달하기 전, 응답이 클라이언트에 돌아가기 전에 끼어드는 공통 처리 레이어.

---

## 요청/응답 흐름

```
클라이언트 요청
      │
      ▼
 [Middleware 1]  ← CORS 검사
      │
      ▼
 [Middleware 2]  ← 로깅
      │
      ▼
  Router/Handler  ← 실제 비즈니스 로직
      │
      ▼
 [Middleware 2]  ← (역순으로 통과)
      │
      ▼
 [Middleware 1]
      │
      ▼
클라이언트 응답
```

요청은 위→아래, 응답은 아래→위. 양방향 파이프.

---

## Spring 비유

| Spring | FastAPI |
|--------|---------|
| `Filter` (서블릿 레벨) | `Middleware` |
| `HandlerInterceptor` | `Middleware` or `Depends()` |
| `@ControllerAdvice` | `exception_handler` |

---

## CORSMiddleware 예시

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

모든 요청이 라우터 도달 전에 CORS 헤더 검사·추가. 개별 라우터마다 처리 불필요.

---

## Middleware vs Depends() 차이

| | Middleware | `Depends()` |
|---|---|---|
| **적용 범위** | 앱 전체 모든 요청 | 특정 라우터/엔드포인트 |
| **주 용도** | CORS, 로깅, 압축 등 공통 처리 | JWT 인증, DB 세션 주입 등 |

CORS처럼 "모든 요청에 무조건 적용"은 Middleware, "이 엔드포인트는 로그인한 사람만"은 `Depends()`.
