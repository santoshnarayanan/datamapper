import uuid
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.models.base import Base


class EbaTemplate(Base):
    __tablename__ = "ebatemplate"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    structure = Column(JSONB, nullable=False)