import enum
import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import UUID, DateTime, Enum, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class NodeType(str, enum.Enum):
    P = "P"
    C = "C"
    M = "M"
    D = "D"


class NodeStatus(str, enum.Enum):
    draft = "draft"
    confirmed = "confirmed"
    rejected = "rejected"


class NodeModel(Base):
    __tablename__ = "nodes"
    __table_args__ = (
        UniqueConstraint("space_id", "node_type", "label", name="uq_nodes_space_type_label"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    space_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    node_type: Mapped[NodeType] = mapped_column(Enum(NodeType, name="node_type"), nullable=False)
    label: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[NodeStatus] = mapped_column(Enum(NodeStatus, name="node_status"), default=NodeStatus.draft, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)
    embedding_model: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
