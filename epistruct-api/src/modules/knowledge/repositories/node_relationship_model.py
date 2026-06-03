import enum
import uuid
from datetime import datetime

from sqlalchemy import UUID, DateTime, Enum, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class RelationType(str, enum.Enum):
    DECOMPOSE_TO = "DECOMPOSE_TO"
    MANIFESTS_AS = "MANIFESTS_AS"
    INSTANTIATED_BY = "INSTANTIATED_BY"
    CONNECTS_TO = "CONNECTS_TO"
    ANALOGOUS_TO = "ANALOGOUS_TO"
    BELONGS_TO = "BELONGS_TO"


class NodeRelationshipModel(Base):
    __tablename__ = "node_relationships"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    space_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    from_node_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    to_node_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    relation_type: Mapped[RelationType] = mapped_column(Enum(RelationType, name="relation_type"), nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
