import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field


class SupabaseWebhookRecord(BaseModel):
    id: uuid.UUID
    email: str | None = None
    raw_user_meta_data: dict[str, Any] = Field(default_factory=dict)


class SupabaseWebhookPayload(BaseModel):
    type: Literal["INSERT", "UPDATE", "DELETE"]
    table: str
    schema_name: str = Field(alias="schema")
    record: SupabaseWebhookRecord | None = None
    old_record: SupabaseWebhookRecord | None = None

    model_config = {"populate_by_name": True}


class UserProfileResponse(BaseModel):
    id: uuid.UUID
    display_name: str


class UserProfileUpdateRequest(BaseModel):
    display_name: str
