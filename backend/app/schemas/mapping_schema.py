from pydantic import BaseModel, Field, validator
from typing import List, Optional
from uuid import UUID


# ===============================
# COLUMN REFERENCE
# ===============================
class ColumnRef(BaseModel):
    worksheet: str = Field(..., min_length=1)
    column: str = Field(..., min_length=1)

    @validator("worksheet", "column")
    def strip_values(cls, v):
        return v.strip()


# ===============================
# MAPPING ITEM
# ===============================
class MappingItem(BaseModel):
    id: Optional[str] = None

    source: ColumnRef
    target: ColumnRef

    # 🔥 ADD THIS (Phase 7 compatibility)
    confidence: Optional[float] = Field(None, ge=0, le=1)
    method: Optional[str] = Field(None)

    # 🔥 STRICT STATUS CONTROL
    status: str = Field(default="MAPPED")

    @validator("status")
    def validate_status(cls, v):
        allowed = {"MAPPED", "REJECTED", "SUGGESTED"}
        if v not in allowed:
            raise ValueError(f"Invalid status: {v}")
        return v


# ===============================
# REQUEST MODEL
# ===============================
class MappingRequest(BaseModel):
    workflow_id: UUID

    source_worksheet: str = Field(..., min_length=1)
    target_worksheet: str = Field(..., min_length=1)

    mapping: List[MappingItem]

    @validator("mapping")
    def validate_non_empty(cls, v):
        if not v:
            raise ValueError("Mapping list cannot be empty")
        return v