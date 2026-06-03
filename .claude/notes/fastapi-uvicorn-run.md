---
date: 2026-06-03
tags: [fastapi, uvicorn, uv, venv, spring]
---

# FastAPI 실행 구조 — Uvicorn, uv, 가상환경

## 핵심 개념
FastAPI는 WAS를 내장하지 않는다. Uvicorn을 별도로 띄워야 하고, uv가 Python 환경 격리를 담당한다.

---

## Spring vs FastAPI 실행 구조 비교

```
# Spring
JVM → Tomcat(WAS) → Spring Application

# FastAPI
Python → Uvicorn(WAS) → FastAPI Application
```

Tomcat 자리에 Uvicorn이 있다. Spring은 WAS가 내장돼있지만 FastAPI는 별도로 띄워야 한다.

---

## uvicorn 실행 명령

```bash
uvicorn src.main:app --reload
#        ^^^^^^^^^^ 모듈경로:FastAPI인스턴스변수명
#                        ^^^^^^^^ main.py의 app = create_app()
```

`--reload`: 코드 변경 시 자동 재시작 — Spring DevTools hot reload와 동일. 개발 환경에서만 사용.

---

## uv가 하는 역할

Python은 "어떤 Python으로, 어떤 패키지가 설치된 환경에서 실행하느냐"를 먼저 잡아야 한다.
이것이 **가상환경(venv)**이고, uv가 프로젝트마다 `.venv/` 폴더를 만들어 격리해준다.

```
프로젝트A: Python 3.12, fastapi 0.115  ← .venv/
프로젝트B: Python 3.11, fastapi 0.110  ← .venv/
```

```bash
uv run uvicorn src.main:app
# ^^^^^^^^
# ".venv 안의 Python으로 uvicorn을 실행해라"
```

`uv run`을 앞에 붙이면 해당 프로젝트의 격리된 환경에서 실행된다.

---

## 실행 방법 3가지

```bash
# 1. uv run (권장 — 환경 자동)
uv run uvicorn src.main:app --reload

# 2. 가상환경 직접 활성화 후 실행
source .venv/bin/activate    # Mac/Linux
uvicorn src.main:app --reload

# 3. PyCharm Run Configuration
# Script: uvicorn src.main:app --reload 등록 후 IDE에서 클릭 실행
```

---

## 운영 환경 실행

```bash
# 개발
uvicorn src.main:app --reload --port 8000

# 운영 (reload 제거, workers 추가)
uvicorn src.main:app --workers 4 --port 8000

# 더 안정적인 운영 (Gunicorn + Uvicorn worker)
gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

Spring의 `java -jar app.jar --spring.profiles.active=prod`처럼 환경별 옵션이 달라진다.

---

## 관련 개념
- `uv.lock` — 패키지 버전 고정 파일. 누가 언제 설치해도 동일한 환경 보장
- `pyproject.toml` — 프로젝트 의존성 선언 파일 (Maven pom.xml / Gradle build.gradle 역할)
