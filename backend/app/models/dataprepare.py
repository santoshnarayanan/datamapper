import uuid
from sqlalchemy import Column, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.models.base import Base


class DataPrepare(Base):
    __tablename__ = "dataprepare"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    workflow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workflow.id", ondelete="CASCADE"),
        nullable=False
    )

    worksheet_id = Column(
        UUID(as_uuid=True),
        ForeignKey("worksheet.id", ondelete="CASCADE"),
        nullable=False
    )

    steps = Column(JSONB)       # operations
    snapshots = Column(JSONB, default=dict)
    execution_logs = Column(JSONB, default=list)# history

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    workflow = relationship("Workflow")
    worksheet = relationship("Worksheet")