---
date: 2026-06-03
tags: [python, type-hints, mypy, fastapi]
---

# Python 타입 힌트 (Type Hints)

## 핵심 개념
함수 반환 타입, 파라미터, 변수에 타입을 명시하는 문법. 강제가 아닌 힌트이며 mypy가 정적 분석으로 체크한다.

---

## 함수 반환 타입 — `-> ReturnType`

```python
def create_app() -> FastAPI:   # FastAPI 인스턴스를 반환한다고 명시
    ...
```

Java 비교:
```java
FastAPI createApp() { ... }   // Java는 반환 타입이 앞에 옴
```
Python은 반환 타입을 **뒤에** `->` 로 쓴다. 위치만 다르고 의미는 같다.

---

## 타입 힌트는 강제가 아니다

Java처럼 컴파일러가 체크하지 않는다. 어겨도 런타임 에러가 나지 않는다.

```python
def create_app() -> FastAPI:
    return "hello"   # 힌트 위반이지만 실행은 됨
```

**그러면 왜 쓰나?**
- `mypy` 같은 정적 분석 도구가 힌트 기반으로 오류를 잡아준다
- IDE 자동완성이 정확해진다
- `pyproject.toml`에 mypy가 설정된 이유가 여기 있다

---

## 파라미터 + 반환값 + 변수 타입 힌트

```python
# 파라미터 + 반환값
def greet(name: str) -> str:
    return f"Hello {name}"

# 변수
user_id: str = "abc-123"
count: int = 0

# 힌트 생략도 가능 (선택사항)
user_id = "abc-123"
```

Java 비교:
```java
String greet(String name) { return "Hello " + name; }
String userId = "abc-123";
```

같은 의미. Python은 타입이 뒤에 오고 선택사항이라는 차이만 있다.

---

## uvicorn 진입점과의 연결

```python
def create_app() -> FastAPI:
    app = FastAPI(...)
    ...
    return app

app = create_app()   # 모듈 최상단에서 한 번 실행
```

uvicorn 실행 시:
```bash
uvicorn src.main:app --reload
#               ^^^^ src/main.py의 app 변수를 찾음
```

`src.main` 모듈의 `app` 변수를 서버 진입점으로 사용한다.

---

## 관련 개념
- `mypy` — Python 정적 타입 체커. `pyproject.toml`의 `[tool.mypy]`에서 설정
- `create_app()` 팩토리 패턴 — Spring의 `@Configuration` + `@Bean` 조합과 유사
