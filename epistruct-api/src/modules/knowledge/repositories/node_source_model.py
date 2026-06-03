import uuid

from sqlalchemy import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class NodeSourceModel(Base):
    __tablename__ = "node_sources"

    node_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
