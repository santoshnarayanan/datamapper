from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID


class ColumnRef(BaseModel):
    worksheet: str
    column: str


class MappingItem(BaseModel):
    id: Optional[str] = None
    source: ColumnRef
    target: ColumnRef
    status: str = "MAPPED"


class MappingRequest(BaseModel):
    workflow_id: UUID
    source_worksheet: str
    target_worksheet: str
    mapping: List[MappingItem]