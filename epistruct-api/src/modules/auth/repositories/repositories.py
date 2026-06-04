import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.domain.entities import User
from src.modules.auth.domain.repositories import UserRepository
from src.modules.auth.repositories.user_model import UserModel


class SqlUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user_id, UserModel.deleted_at.is_(None))
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def upsert(self, user: User) -> User:
        stmt = (
            insert(UserModel)
            .values(
                id=user.id,
                display_name=user.display_name,
            )
            .on_conflict_do_update(
                index_elements=["id"],
                set_={"display_name": user.display_name, "deleted_at": None},
            )
            .returning(UserModel)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one()
        await self._session.flush()
        return _to_entity(model)

    async def soft_delete(self, user_id: uuid.UUID) -> None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.deleted_at = datetime.now(timezone.utc)
            await self._session.flush()


def _to_entity(model: UserModel) -> User:
    return User(
        id=model.id,
        display_name=model.display_name,
        personal_space_id=model.personal_space_id,
        default_strategy_id=model.default_strategy_id,
        created_at=model.created_at,
        deleted_at=model.deleted_at,
    )
