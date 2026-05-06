import uuid
from sqlalchemy import Column, TIMESTAMP, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.models.base import Base


class MappingInfo(Base):
    __tablename__ = "mappinginfo"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    workflow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workflow.id", ondelete="CASCADE"),
        nullable=False
    )

    # 🔥 NEW FIELDS (IMPORTANT)
    source_worksheet = Column(String, nullable=False)
    target_worksheet = Column(String, nullable=False)

    mapping = Column(JSONB, nullable=False)

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    decision_trace = Column(JSONB, nullable=True)

    workflow = relationship("Workflow")