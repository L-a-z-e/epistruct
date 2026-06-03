# Git 워크플로우 규칙

## 브랜치 전략

```
main  ──── 프로덕션. 언제나 릴리즈 가능 상태. 직접 커밋 금지.
  └─ dev ── 다음 릴리즈 통합 브랜치. 모든 작업 브랜치가 여기로 머지됨.
       └─ feature/xxx   새 기능
       └─ fix/xxx       버그 수정
       └─ refactor/xxx  리팩토링
       └─ docs/xxx      문서
       └─ chore/xxx     설정·빌드
```

- **모든 작업은 `dev` 기준으로 브랜치를 생성한다** — 문서 작업 포함 예외 없음
- `main`은 릴리즈 시에만 `dev` → `main` PR로 머지

## 브랜치 네이밍

```
<type>/<short-description>
```

- 소문자, 하이픈(-) 구분, 영어만
- 이슈 번호 등 의미 없는 숫자 포함 금지
- 설명 2~4단어
- 예: `feature/backend-project-setup`, `fix/auth-token-expiry`, `docs/api-spec-update`

## 브랜치 생성 전 필수 절차

브랜치를 새로 딸 때 반드시 아래 순서로 실행한다.

```bash
# 1. 원격 최신 상태 동기화
git fetch origin

# 2. base 브랜치(dev) 최신화
git checkout dev
git pull origin dev

# 3. 새 브랜치 생성
git checkout -b feature/xxx
```

원격과 동기화 없이 브랜치를 생성하면 버전이 꼬일 수 있다. 생략 금지.

## Push / PR 규칙

- **push는 사용자 명시 확인 후에만 실행** — feature, dev, main 모두 동일
- **PR 생성도 사용자 명시 확인 후에만 실행**
- push 또는 PR이 필요한 시점이 되면 "push 해도 될까요?" / "PR 생성해도 될까요?" 로 먼저 묻는다
- 사용자가 먼저 push/PR을 요청하지 않는 이상 자동으로 실행하지 않는다

## 커밋 메시지

```
<type>(<scope>): <subject>

[body]
```

- subject: 50자 이내, 명령형, 소문자 시작, 마침표 없음
- body: What & Why 중심, 72자 줄바꿈
- Co-Authored-By, AI 도구명 관련 내용을 커밋 메시지·PR·코드 주석 어디에도 절대 추가 금지
- Types: feat, fix, docs, style, refactor, test, chore, perf, ci
