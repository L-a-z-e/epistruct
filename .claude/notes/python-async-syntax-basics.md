---
date: 2026-06-03
tags: [python, async, asynccontextmanager, yield, fastapi]
---

# Python 비동기 문법 기초 (asynccontextmanager, yield, async with, pass)

## 핵심 개념
FastAPI의 lifespan 패턴을 이해하기 위한 Python 비동기 문법 4가지 — yield, async with, pass, @asynccontextmanager

---

## yield — 함수를 일시정지시키는 키워드

`yield`가 있는 함수는 **제너레이터**가 된다. Java에는 없는 개념.

```python
def countdown():
    print("시작")
    yield          # 여기서 멈춤. 호출자에게 제어권 반환
    print("끝")   # 나중에 다시 재개될 때 실행
```

`yield` 전/후로 코드를 쪼갤 수 있다. "여기까지 실행하고 잠깐 멈춰, 나중에 다시 와서 나머지 실행해" 라는 의미.

---

## with — 자원을 자동으로 열고 닫는 문법

Java의 `try-with-resources`와 동일한 개념.

```java
// Java
try (Connection conn = dataSource.getConnection()) {
    // conn 사용
} // 자동으로 conn.close() 호출
```

```python
# Python
with open("file.txt") as f:
    # f 사용
# 블록 나가면 자동으로 f.close() 호출
```

`async with`는 비동기 버전. DB 연결처럼 I/O가 있으면 앞에 `async`가 붙는다.

```python
async with engine.connect() as conn:
    # DB 연결 사용
# 블록 나가면 자동으로 연결 반납
```

---

## pass — 아무것도 안 하는 자리채우기

Python은 빈 블록을 문법 오류로 본다. 내용 없이 구조만 잡을 때 사용.

```python
# 문법 오류
if True:
    # 비어있음

# OK
if True:
    pass
```

실제 사용 예 (main.py):
```python
async with engine.connect():
    pass   # 연결만 시도, 실제 쿼리는 안 함
           # 연결 성공 = DB가 살아있다는 증거
```

---

## @asynccontextmanager — yield로 with문을 직접 만드는 데코레이터

`with`문을 직접 만들려면 원래 `__enter__`, `__exit__` 메서드를 가진 클래스가 필요하다.  
`@asynccontextmanager`는 그걸 `yield` 하나로 대체해준다.

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # yield 앞: with 블록 진입 시 실행 (= __enter__)
    async with engine.connect():
        pass

    yield   # ← FastAPI가 여기서 앱을 실행시킴 (요청 받기 시작)

    # yield 뒤: with 블록 종료 시 실행 (= __exit__)
    await engine.dispose()
```

FastAPI lifespan 흐름:
```
서버 시작
  │
  ▼
yield 앞 실행   ← DB 연결 확인
  │
  ▼
yield          ← FastAPI가 요청 받기 시작
  │
  ▼ (종료 신호)
yield 뒤 실행  ← 연결 풀 정리
  │
  ▼
서버 종료
```

Spring 비유:
- `yield` 앞 = `@PostConstruct` (빈 초기화 후)
- `yield` 뒤 = `@PreDestroy` (컨테이너 종료 전)

---

## @ 데코레이터

함수를 감싸서 기능을 추가하는 문법. Spring의 `@Transactional`, `@Cacheable`과 같은 개념.

```python
@asynccontextmanager   # lifespan 함수를 context manager로 변환
async def lifespan(app: FastAPI):
    ...

# @ 없이 쓰면 이것과 동일
lifespan = asynccontextmanager(lifespan)
```

---

## 관련 개념
- FastAPI `lifespan` 파라미터 — `create_app()`에서 `FastAPI(lifespan=lifespan)`으로 등록
- `await engine.dispose()` — SQLAlchemy 비동기 엔진의 연결 풀 반납 메서드
- `async def` — 비동기 함수 선언. `await`를 쓸 수 있는 함수
