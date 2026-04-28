from sqlalchemy import Column, String, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.models.base import Base


class MappingFeedback(Base):
    __tablename__ = "mapping_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), nullable=False)

    source_field = Column(Text, nullable=False)
    suggested_field = Column(Text)
    final_field = Column(Text, nullable=False)

    action = Column(String, nullable=False)  # ACCEPT / REJECT

    created_at = Column(TIMESTAMP, server_default=func.now())