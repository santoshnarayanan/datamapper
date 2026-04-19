import uuid

from sqlalchemy import Column, String, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.models.base import Base

class Worksheet(Base):
    __tablename__ = "worksheet"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    workflow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workflow.id", ondelete="CASCADE"),  # ✅ FIX
        nullable=False
    )

    name = Column(String)
    data = Column(JSONB, nullable=False)

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    workflow = relationship("Workflow", backref="worksheets")

