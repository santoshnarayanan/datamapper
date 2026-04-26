from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

from app.core.database import get_db
from app.models.worksheet import Worksheet
from app.repositories.mapping_repo import  save_or_update_mapping
from app.schemas.mapping_schema import MappingRequest
from app.models import EbaTemplate
from app.repositories.mapping_repo import get_mapping
from app.services.mapping_validation_service import validate_mapping_request
from app.services.mapping_execution_service import execute_mapping
from app.services.export_service import generate_excel, generate_csv
from app.services.dataprepare_service import get_latest_dataprepare_snapshot
from app.services.vector_mapping_service import store_mapping_history

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

    snapshot = get_latest_dataprepare_snapshot(db, str(workflow_id), worksheet.id)

    if snapshot:
        source_data = snapshot
    else:
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

    # =========================================
    # 🔹 FETCH SOURCE + TARGET FOR VALIDATION
    # =========================================
    worksheet = db.query(Worksheet).filter(
        Worksheet.workflow_id == request.workflow_id,
        Worksheet.name == request.source_worksheet
    ).order_by(Worksheet.version.desc()).first()

    if not worksheet:
        raise HTTPException(status_code=404, detail="Source worksheet not found")

    eba_template = db.query(EbaTemplate).filter(
        EbaTemplate.name == request.target_worksheet
    ).first()

    if not eba_template:
        raise HTTPException(status_code=404, detail="Target worksheet not found")

    snapshot = get_latest_dataprepare_snapshot(
        db,
        str(request.workflow_id),
        worksheet.id
    )

    if snapshot:
        source_columns = snapshot.get("columns", [])
    else:
        source_columns = worksheet.data.get("columns", [])
    target_columns = eba_template.structure.get("columns", [])

    # =========================================
    # 🔥 VALIDATION STEP
    # =========================================
    validate_mapping_request(
        [m.dict() for m in request.mapping],
        source_columns,
        target_columns,
        request.source_worksheet,
        request.target_worksheet
    )

    # =========================================
    # 🔹 SAVE
    # =========================================
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

@router.get("/mapping-execute/{workflow_id}")
def execute_mapping_api(
    workflow_id: str,
    source_ws: str,
    target_ws: str,
    db: Session = Depends(get_db)
):

    # =========================================
    # 🔹 SOURCE
    # =========================================
    worksheet = db.query(Worksheet).filter(
        Worksheet.workflow_id == workflow_id,
        Worksheet.name == source_ws
    ).order_by(Worksheet.version.desc()).first()

    if not worksheet:
        return {"error": "Source worksheet not found"}

    # 🔥 NEW: Use DataPrepare snapshot
    snapshot = get_latest_dataprepare_snapshot(db, str(workflow_id), worksheet.id)

    if snapshot:
        source_rows = snapshot.get("rows", [])
    else:
        source_data = worksheet.data or {}
        source_rows = source_data.get("rows", [])

    # =========================================
    # 🔹 MAPPING
    # =========================================
    mapping_record = get_mapping(db, workflow_id, source_ws, target_ws)

    if not mapping_record:
        return {
            "data": [],
            "message": "No mapping found"
        }

    mapping = mapping_record.mapping

    # =========================================
    # 🔥 EXECUTION
    # =========================================
    result = execute_mapping(source_rows, mapping)

    return {
        "data": result,
        "count": len(result)
    }

@router.get("/mapping-export/{workflow_id}")
def export_mapping(
    workflow_id: str,
    source_ws: str,
    target_ws: str,
    format: str = "excel",  # excel or csv
    db: Session = Depends(get_db)
):

    # =========================================
    # 🔹 SOURCE
    # =========================================
    worksheet = db.query(Worksheet).filter(
        Worksheet.workflow_id == workflow_id,
        Worksheet.name == source_ws
    ).order_by(Worksheet.version.desc()).first()

    if not worksheet:
        return {"error": "Source worksheet not found"}

    snapshot = get_latest_dataprepare_snapshot(db, str(workflow_id), worksheet.id)

    if snapshot:
        source_rows = snapshot.get("rows", [])
    else:
        source_rows = worksheet.data.get("rows", [])

    # =========================================
    # 🔹 MAPPING
    # =========================================
    mapping_record = get_mapping(db, workflow_id, source_ws, target_ws)

    if not mapping_record:
        return {"error": "No mapping found"}

    mapping = mapping_record.mapping

    # =========================================
    # 🔹 EXECUTE
    # =========================================
    result = execute_mapping(source_rows, mapping)

    # =========================================
    # 🔥 EXPORT
    # =========================================
    if format == "excel":
        file = generate_excel(result)
        filename = "mapping_output.xlsx"
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    elif format == "csv":
        file = generate_csv(result)
        filename = "mapping_output.csv"
        media_type = "text/csv"

    else:
        return {"error": "Invalid format. Use 'excel' or 'csv'"}

    return StreamingResponse(
        file,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/mapping-suggestions/{workflow_id}")
def get_mapping_suggestions(
    workflow_id: str,
    source_ws: str,
    target_ws: str,
    db: Session = Depends(get_db)
):

    # =========================================
    # 🔹 SOURCE
    # =========================================
    worksheet = db.query(Worksheet).filter(
        Worksheet.workflow_id == workflow_id,
        Worksheet.name == source_ws
    ).order_by(Worksheet.version.desc()).first()

    if not worksheet:
        return {"error": "Source worksheet not found"}

    snapshot = get_latest_dataprepare_snapshot(
        db,
        str(workflow_id),
        worksheet.id
    )

    if snapshot:
        source_columns = snapshot.get("columns", [])
    else:
        source_columns = worksheet.data.get("columns", [])

    # =========================================
    # 🔹 TARGET
    # =========================================
    eba_template = db.query(EbaTemplate).filter(
        EbaTemplate.name == target_ws
    ).first()

    if not eba_template:
        return {"error": "Target worksheet not found"}

    target_columns = eba_template.structure.get("columns", [])

    # =========================================
    # 🔥 SUGGESTIONS
    # =========================================
    from app.services.mapping_suggestion_service import suggest_mappings

    suggestions = suggest_mappings(source_columns, target_columns)

    return {
        "suggestions": suggestions
    }

# Persist mapping history in Pinecone to improve future matching accuracy
@router.post("/mapping-auto/{workflow_id}")
def auto_mapping(
    workflow_id: str,
    source_ws: str = Query(...),
    target_ws: str = Query(...),
    db: Session = Depends(get_db)
):

    # =========================================
    # 🔹 SOURCE
    # =========================================
    worksheet = db.query(Worksheet).filter(
        Worksheet.workflow_id == workflow_id,
        Worksheet.name == source_ws
    ).order_by(Worksheet.version.desc()).first()

    if not worksheet:
        return {"error": "Source worksheet not found"}

    snapshot = get_latest_dataprepare_snapshot(
        db,
        str(workflow_id),
        worksheet.id
    )

    if snapshot:
        source_columns = snapshot.get("columns", [])
    else:
        source_columns = (worksheet.data or {}).get("columns", [])

    # =========================================
    # 🔹 TARGET
    # =========================================
    eba_template = db.query(EbaTemplate).filter(
        EbaTemplate.name == target_ws
    ).first()

    if not eba_template:
        return {"error": "Target worksheet not found"}

    target_columns = eba_template.structure.get("columns", [])

    # =========================================
    # 🔥 AGENT EXECUTION
    # =========================================

    # below code is commnented for Step 7.7A (rule based only)
    # from app.services.mapping_agent_service import run_mapping_agent
    #
    # generated_mapping = run_mapping_agent(
    #     source_columns,
    #     target_columns,
    #     source_ws,
    #     target_ws
    # )

    from app.services.mapping_agent_service import run_hybrid_mapping_agent

    generated_mapping = run_hybrid_mapping_agent(
        source_columns,
        target_columns,
        source_ws,
        target_ws
    )

    # =========================================
    # 🔹 VALIDATION
    # =========================================
    validate_mapping_request(
        generated_mapping,
        source_columns,
        target_columns,
        source_ws,
        target_ws
    )

    # =========================================
    # 🔹 SAVE (IMPORTANT FIX)
    # =========================================
    saved_mapping = save_or_update_mapping(
        db,
        workflow_id,
        source_ws,
        target_ws,
        generated_mapping
    )

    # Store history after save
    store_mapping_history(saved_mapping.mapping)

    # =========================================
    # 🔹 OBSERVABILITY
    # =========================================
    print("Agent Mapping Generated:", generated_mapping)

    return {
        "status": "success",
        "mapping": saved_mapping.mapping
    }

# Debug endpoint to inspect Pinecone vector matches
# Useful for validating semantic similarity and stored metadata
@router.get("/debug-pinecone")
def debug_pinecone_api(query: str):
    from app.services.embedding_service import get_embedding
    from app.services.pinecone_service import query_vector

    vector = get_embedding(query)
    matches = query_vector(vector, top_k=5)

    return [
        {
            "score": m.score,
            "metadata": m.metadata
        }
        for m in matches
    ]