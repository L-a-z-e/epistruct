import hmac

from fastapi import APIRouter, Depends, Header, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_session
from src.core.exceptions import UnauthorizedError
from src.modules.auth.dependencies import get_current_user
from src.modules.auth.domain.entities import User
from src.modules.auth.repositories.repositories import SqlUserRepository
from src.modules.auth.schemas import SupabaseWebhookPayload, UserProfileResponse, UserProfileUpdateRequest
from src.modules.auth.services.services import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/webhook", status_code=status.HTTP_204_NO_CONTENT)
async def supabase_webhook(
    payload: SupabaseWebhookPayload,
    x_webhook_secret: str | None = Header(None),
    session: AsyncSession = Depends(get_session),
) -> None:
    if not _verify_secret(x_webhook_secret):
        raise UnauthorizedError(message="Invalid webhook secret")

    # DELETE는 record가 null, old_record에 삭제된 데이터가 있음
    if payload.type == "DELETE":
        if payload.old_record is None:
            return
        record_data = payload.old_record.model_dump()
    else:
        if payload.record is None:
            return
        record_data = payload.record.model_dump()

    service = UserService(SqlUserRepository(session))
    old = payload.old_record.model_dump() if payload.old_record else None
    await service.handle_webhook(payload.type, record_data, old)
    await session.commit()


@router.get("/me", response_model=UserProfileResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> UserProfileResponse:
    return UserProfileResponse(id=current_user.id, display_name=current_user.display_name)


@router.patch("/me", response_model=UserProfileResponse)
async def update_me(
    body: UserProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> UserProfileResponse:
    service = UserService(SqlUserRepository(session))
    updated = await service.update_display_name(current_user.id, body.display_name)
    await session.commit()
    return UserProfileResponse(id=updated.id, display_name=updated.display_name)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    service = UserService(SqlUserRepository(session))
    await service.delete_user(current_user.id)
    await session.commit()


def _verify_secret(received: str | None) -> bool:
    if not settings.supabase_webhook_secret:
        return True  # 시크릿 미설정 시 개발 환경으로 간주
    if not received:
        return False
    return hmac.compare_digest(received, settings.supabase_webhook_secret)
