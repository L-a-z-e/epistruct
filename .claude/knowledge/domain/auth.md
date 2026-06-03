# 인증 — Supabase Auth 연동

## 아키텍처

```
Expo 클라이언트
  → Supabase Auth SDK로 로그인 (소셜/이메일)
  → Supabase가 JWT 발급
  → FastAPI 요청 시 Authorization: Bearer <JWT>
  → FastAPI auth 미들웨어: Supabase JWKS endpoint로 토큰 검증
  → 검증된 user_id(UUID)로 내 PostgreSQL 조회
```

## auth 모듈 역할 분담

```
Supabase가 담당:
  - 로그인 / 가입 / 토큰 발급
  - Refresh token rotation
  - 이메일 인증

auth 모듈(FastAPI)이 담당:
  - JWT 검증 미들웨어 (Supabase JWKS 사용)
  - users 테이블 CRUD (프로필, personal_space_id, 학습 스타일)
  - Supabase webhook 수신 엔드포인트 (가입 시 users 행 자동 생성)
```

## 내 DB와의 연동

```sql
-- Supabase auth.users: Supabase가 관리 (직접 접근 최소화)
-- 내 PostgreSQL users 테이블: 프로필 + 앱 데이터

users
  id                UUID PK  -- Supabase user_id와 동일
  personal_space_id UUID     -- 개인 공간 빠른 조회용
  display_name      VARCHAR
  learning_style    JSONB    -- 온보딩 결과 (Phase 1-B)
  created_at        TIMESTAMPTZ
  deleted_at        TIMESTAMPTZ
```

**가입 흐름**: Supabase webhook → `/internal/auth/webhook` → users 행 생성 + personal space 생성 + space_members에 owner로 등록 (트랜잭션).

## JWT 검증 미들웨어

```python
# FastAPI dependency
async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserID:
    # Supabase JWKS endpoint로 검증
    # 검증 실패 → 401
    # 성공 → user_id(UUID) 반환
```

## 사용자 식별

모든 코드에서 사용자 식별은 `user_id`(UUID)로 통일.
Supabase의 이메일, 소셜 계정 등은 auth 모듈 내부에서만 다룬다.
