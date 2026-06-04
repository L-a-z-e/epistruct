import uuid

from src.modules.auth.domain.entities import User
from src.modules.auth.domain.repositories import UserRepository


class UserService:
    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo

    async def get_or_create(self, user_id: uuid.UUID, fallback_name: str = "User") -> User:
        user = await self._repo.get_by_id(user_id)
        if user is None:
            user = await self._repo.upsert(User(id=user_id, display_name=fallback_name))
        return user

    async def update_display_name(self, user_id: uuid.UUID, display_name: str) -> User:
        user = await self._repo.get_by_id(user_id)
        if user is None:
            from src.core.exceptions import NotFoundError
            raise NotFoundError(code="AUTH_USER_NOT_FOUND", message="User not found")
        user.display_name = display_name
        return await self._repo.upsert(user)

    async def delete_user(self, user_id: uuid.UUID) -> None:
        await self._repo.soft_delete(user_id)

    async def handle_webhook(self, event_type: str, record: dict, old_record: dict | None) -> None:
        raw_id = record["id"]
        user_id = raw_id if isinstance(raw_id, uuid.UUID) else uuid.UUID(str(raw_id))
        if event_type in ("INSERT", "UPDATE"):
            meta = record.get("raw_user_meta_data") or {}
            email: str = record.get("email") or ""
            display_name = meta.get("display_name") or meta.get("name") or email.split("@")[0] or "User"
            await self._repo.upsert(User(id=user_id, display_name=display_name))
        elif event_type == "DELETE":
            await self._repo.soft_delete(user_id)
