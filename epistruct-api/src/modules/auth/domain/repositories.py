import uuid
from abc import ABC, abstractmethod

from src.modules.auth.domain.entities import User


class UserRepository(ABC):
    @abstractmethod
    async def get_by_id(self, user_id: uuid.UUID) -> User | None: ...

    @abstractmethod
    async def upsert(self, user: User) -> User: ...

    @abstractmethod
    async def soft_delete(self, user_id: uuid.UUID) -> None: ...
