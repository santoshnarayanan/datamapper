from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.worksheet import Worksheet
from app.repositories.mapping_repo import get_mapping, save_or_update_mapping
from app.repositories.ebatemplate_repo import get_eba_template
from app.schemas.mapping_schema import MappingRequest
from app.models import EbaTemplate
from app.repositories.mapping_repo import get_mapping
from app.services.mapping_screen_service import (
    get_latest_worksheet,
    get_all_source_worksheets,
    get_all_target_templates,
    get_target_template
)

router = APIRouter()

from fastapi import Query

@router.get("/mapping-screen/{workflow_id}")
def get_mapping_screen(
    workflow_id: str,
    source_ws: str = Query(...),
    target_ws: str = Query(...),
    db: Session = Depends(get_db)
):

    # =========================================
    # 🔹 SOURCE (Latest Worksheet)
    # =========================================
    worksheet = db.query(Worksheet).filter(
        Worksheet.workflow_id == workflow_id,
        Worksheet.name == source_ws
    ).order_by(Worksheet.version.desc()).first()

    if not worksheet:
        return {"error": f"Source worksheet '{source_ws}' not found"}

    source_data = worksheet.data or {}

    # =========================================
    # 🔹 TARGET (FIXED: filter by name)
    # =========================================
    eba_template = db.query(EbaTemplate).filter(
        EbaTemplate.name == target_ws
    ).first()

    if not eba_template:
        return {"error": f"Target worksheet '{target_ws}' not found"}

    target_data = eba_template.structure or {}

    # =========================================
    # 🔹 MAPPING
    # =========================================
    mapping_record = get_mapping(db, workflow_id, source_ws, target_ws)
    mapping = mapping_record.mapping if mapping_record else []

    # =========================================
    # 🔹 META (NEW)
    # =========================================
    source_ws_list = list(set([
        w.name for w in db.query(Worksheet).filter(
            Worksheet.workflow_id == workflow_id
        ).all()
    ]))

    target_ws_list = [
        t.name for t in db.query(EbaTemplate).all()
    ]

    # =========================================
    # 🔹 FINAL RESPONSE (STRUCTURED)
    # =========================================
    return {
        "source": {
            "worksheet": source_ws,
            "columns": source_data.get("columns", []),
            "rows": source_data.get("rows", [])
        },
        "target": {
            "worksheet": target_ws,
            "columns": target_data.get("columns", [])
        },
        "mapping": mapping,
        "meta": {
            "available_source_worksheets": source_ws_list,
            "available_target_worksheets": target_ws_list,
            "source_worksheet": source_ws,
            "target_worksheet": target_ws
        }
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