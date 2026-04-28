# app/models/worksheet_rows.py

import uuid
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.models.base import Base

class WorksheetRow(Base):
    __tablename__ = "worksheet_rows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worksheet_id = Column(UUID(as_uuid=True), ForeignKey("worksheet.id", ondelete="CASCADE"))
    row_index = Column(Integer, nullable=False)
    row_data = Column(JSONB, nullable=False)