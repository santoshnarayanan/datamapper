from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.worksheet import Worksheet
from app.repositories.mapping_repo import get_mapping, save_or_update_mapping
from app.repositories.ebatemplate_repo import get_eba_template
from app.schemas.mapping_schema import MappingRequest

router = APIRouter()

@router.get("/mapping-screen/{workflow_id}")
def get_mapping_screen(
    workflow_id: str,
    source_ws: str,
    target_ws: str,
    db: Session = Depends(get_db)
):

    # 🔹 Get latest worksheet by name
    worksheet = db.query(Worksheet).filter(
        Worksheet.workflow_id == workflow_id,
        Worksheet.name == source_ws
    ).order_by(Worksheet.version.desc()).first()

    if not worksheet:
        return {"error": "Worksheet not found"}

    # 🔹 Get EBA template (filter by name if needed)
    eba_template = get_eba_template(db)

    # 🔹 Get mapping
    mapping = get_mapping(db, workflow_id, source_ws, target_ws)

    return {
        "source": worksheet.data,
        "target": eba_template.structure if eba_template else {},
        "mapping": mapping.mapping if mapping else []
    }


@router.post("/mapping")
def save_mapping(
    request: MappingRequest,
    db: Session = Depends(get_db)
):

    mapping = save_or_update_mapping(
        db,
        request.workflow_id,
        request.source_worksheet,
        request.target_worksheet,
        [m.dict() for m in request.mapping]
    )

    return {
        "status": "success",
        "mapping": mapping.mapping
    }