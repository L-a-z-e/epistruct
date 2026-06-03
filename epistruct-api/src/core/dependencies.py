from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_session
from src.core.exceptions import UnauthorizedError
from src.core.security import verify_supabase_jwt

bearer_scheme = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    try:
        payload = verify_supabase_jwt(credentials.credentials)
        user_id: str = payload["sub"]
        return user_id
    except (ValueError, KeyError) as e:
        raise UnauthorizedError() from e


CurrentUserId = Depends(get_current_user_id)
