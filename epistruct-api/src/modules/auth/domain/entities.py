import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    id: uuid.UUID
    display_name: str
    personal_space_id: uuid.UUID | None = None
    default_strategy_id: uuid.UUID | None = None
    created_at: datetime | None = None
    deleted_at: datetime | None = None
