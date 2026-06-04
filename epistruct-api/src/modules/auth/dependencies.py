import uuid

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_session
from src.core.exceptions import UnauthorizedError
from src.core.security import verify_supabase_jwt
from src.modules.auth.domain.entities import User
from src.modules.auth.repositories.repositories import SqlUserRepository
from src.modules.auth.services.services import UserService

_bearer = HTTPBearer(auto_error=False)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> uuid.UUID:
    if credentials is None:
        raise UnauthorizedError(message="Authorization header required")
    try:
        payload = verify_supabase_jwt(credentials.credentials)
    except ValueError:
        raise UnauthorizedError(message="Invalid or expired token")
    try:
        return uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        raise UnauthorizedError(message="Token missing subject claim")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    session: AsyncSession = Depends(get_session),
) -> User:
    if credentials is None:
        raise UnauthorizedError(message="Authorization header required")
    try:
        payload = verify_supabase_jwt(credentials.credentials)
    except ValueError:
        raise UnauthorizedError(message="Invalid or expired token")
    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        raise UnauthorizedError(message="Token missing subject claim")

    email: str = payload.get("email", "")
    fallback_name = email.split("@")[0] or "User"

    service = UserService(SqlUserRepository(session))
    user = await service.get_or_create(user_id, fallback_name)
    await session.commit()
    return user
