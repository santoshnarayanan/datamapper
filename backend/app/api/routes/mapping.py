from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

from app.core.database import get_db
from app.models.worksheet import Worksheet
from app.repositories.mapping_repo import save_or_update_mapping
from app.schemas.mapping_schema import MappingRequest
from app.models import EbaTemplate
from app.repositories.mapping_repo import get_mapping
from app.services.mapping_validation_service import validate_mapping_request
from app.services.mapping_execution_service import execute_mapping
from app.services.export_service import generate_excel, generate_csv
from app.services.dataprepare_service import get_latest_dataprepare_snapshot
from app.services.vector_mapping_service import store_mapping_history
from app.repositories.worksheet_row_repo import get_total_rows, get_paginated_rows
from app.services.mapping_agent_service import run_hybrid_mapping_agent
from app.repositories.mapping_feedback_repo import save_feedback

from datetime import datetime
import uuid

router = APIRouter()

from fastapi import Query


@router.get("/mapping-screen/{workflow_id}")
async def get_mapping_screen(
        workflow_id: str,
        source_ws: str = Query(...),
        target_ws: str = Query(...),
        page: int = Query(1),
        page_size: int = Query(50),
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
        EbaTemplate.name == target_ws,
        EbaTemplate.workflow_id == workflow_id
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
        t.name for t in db.query(EbaTemplate).filter(EbaTemplate.workflow_id == workflow_id).all()
    ]

    # =========================================
    # 🔹 ROW FETCHING (NEW LOGIC)
    # =========================================
    if snapshot:
        # Dataprepare exists → fallback to JSON (for now)
        rows = source_data.get("rows", [])
        total = len(rows)

        # Apply pagination at API level
        start = (page - 1) * page_size
        end = start + page_size
        rows = rows[start:end]

    else:
        print("USING DB PAGINATION")
        # No dataprepare → use DB pagination
        rows_db = get_paginated_rows(db, worksheet.id, page, page_size)
        rows = [r.row_data for r in rows_db]
        total = get_total_rows(db, worksheet.id)

    # =========================================
    # 🔹 FINAL RESPONSE (STRUCTURED)
    # =========================================
    return {
        "source": {
            "worksheet": source_ws,
            "columns": source_data.get("columns", []),
            "rows": rows,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size
            }
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
        EbaTemplate.name == request.target_worksheet,
        EbaTemplate.workflow_id == request.workflow_id
    ).first()

    if not eba_template:
        raise HTTPException(status_code=404, detail="Target worksheet not found")

    # =========================================
    # 🔹 GET COLUMNS (SAFE ACCESS)
    # =========================================
    snapshot = get_latest_dataprepare_snapshot(
        db,
        str(request.workflow_id),
        worksheet.id
    )

    original_columns = (worksheet.data or {}).get("columns", [])

    if snapshot:
        snapshot_columns = snapshot.get("columns", [])
        source_columns = list(set(original_columns + snapshot_columns))
    else:
        source_columns = original_columns

    print("SNAPSHOT:", snapshot)
    print("SOURCE COLUMNS USED:", source_columns)

    target_columns = (eba_template.structure or {}).get("columns", [])

    # =========================================
    # 🔥 NEW: PRE-VALIDATION (SCHEMA LEVEL SAFETY)
    # =========================================
    seen_targets = set()
    for m in request.mapping:
        target_col = m.target.column

        if target_col in seen_targets:
            raise HTTPException(
                status_code=400,
                detail=f"Duplicate mapping for target column: {target_col}"
            )
        seen_targets.add(target_col)

    # =========================================
    # 🔥 EXISTING VALIDATION (BUSINESS LOGIC)
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

    # =========================================
    # 🔥 RESPONSE (SLIGHTLY HARDENED)
    # =========================================
    return {
        "status": "success",
        "data": {
            "mapping": mapping.mapping,
            "count": len(mapping.mapping)
        },
        "error": None,
        "meta": {
            "request_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat()
        }
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
        raise HTTPException(status_code=404, detail="Source worksheet not found")

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
    try:
        result = execute_mapping(source_rows, mapping)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    r  # =========================================
    # 🔹 TYPE SAFETY
    # =========================================
    if not isinstance(result, list):
        raise HTTPException(status_code=500, detail="Invalid execution result format")

    return {
        "status": "success",
        "data": {
            "mapping": mapping,
            "result": result,
            "count": len(result)
        },
        "error": None,
        "meta": {
            "request_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat()
        }
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
        raise HTTPException(status_code=404, detail="Source worksheet not found")

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
        raise HTTPException(status_code=404, detail="No mapping found")

    mapping = mapping_record.mapping

    # =========================================
    # 🔹 EXECUTE
    # =========================================
    try:
        result = execute_mapping(source_rows, mapping)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        raise HTTPException(
            status_code=400,
            detail="Invalid format. Use 'excel' or 'csv'"
        )

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
    # 🔹 INPUT VALIDATION
    # =========================================
    if not source_ws.strip() or not target_ws.strip():
        raise HTTPException(
            status_code=400,
            detail="Source and target worksheet names are required"
        )

    # =========================================
    # 🔹 SOURCE
    # =========================================
    worksheet = db.query(Worksheet).filter(
        Worksheet.workflow_id == workflow_id,
        Worksheet.name == source_ws
    ).order_by(Worksheet.version.desc()).first()

    if not worksheet:
        raise HTTPException(status_code=404, detail="Source worksheet not found")

    snapshot = get_latest_dataprepare_snapshot(
        db,
        str(workflow_id),
        worksheet.id
    )

    if snapshot:
        source_columns = snapshot.get("columns", [])
    else:
        source_columns = (worksheet.data or {}).get("columns", [])

    if not source_columns:
        raise HTTPException(
            status_code=400,
            detail="No source columns available"
        )

    # =========================================
    # 🔹 TARGET
    # =========================================
    eba_template = db.query(EbaTemplate).filter(
        EbaTemplate.name == target_ws,
        EbaTemplate.workflow_id == workflow_id
    ).first()

    if not eba_template:
        raise HTTPException(status_code=404, detail="Target worksheet not found")

    target_columns = (eba_template.structure or {}).get("columns", [])

    if not target_columns:
        raise HTTPException(
            status_code=400,
            detail="No target columns available"
        )

    # =========================================
    # 🔥 SUGGESTIONS (SAFE EXECUTION)
    # =========================================
    try:
        from app.services.mapping_suggestion_service import suggest_mappings

        suggestions = suggest_mappings(source_columns, target_columns)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Suggestion engine failed: {str(e)}"
        )

    # =========================================
    # 🔥 VALIDATE OUTPUT STRUCTURE
    # =========================================
    if not isinstance(suggestions, list):
        raise HTTPException(
            status_code=500,
            detail="Invalid response from suggestion engine"
        )

    # Optional: ensure each item has required fields
    for s in suggestions:
        if not isinstance(s, dict):
            raise HTTPException(
                status_code=500,
                detail="Invalid suggestion format"
            )

        if "source" not in s or "target" not in s:
            raise HTTPException(
                status_code=500,
                detail="Malformed suggestion entry"
            )

    # =========================================
    # 🔹 RESPONSE
    # =========================================
    return {
        "status": "success",
        "data": {
            "suggestions": suggestions,
            "count": len(suggestions)
        },
        "error": None,
        "meta": {
            "request_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat()
        }
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
    # 🔹 BASIC INPUT VALIDATION
    # =========================================
    if not source_ws.strip() or not target_ws.strip():
        raise HTTPException(
            status_code=400,
            detail="Source and target worksheet names are required"
        )

    # =========================================
    # 🔹 SOURCE
    # =========================================
    worksheet = db.query(Worksheet).filter(
        Worksheet.workflow_id == workflow_id,
        Worksheet.name == source_ws
    ).order_by(Worksheet.version.desc()).first()

    if not worksheet:
        raise HTTPException(status_code=404, detail="Source worksheet not found")

    snapshot = get_latest_dataprepare_snapshot(
        db,
        str(workflow_id),
        worksheet.id
    )

    if snapshot:
        source_columns = snapshot.get("columns", [])
    else:
        source_columns = (worksheet.data or {}).get("columns", [])

    if not source_columns:
        raise HTTPException(
            status_code=400,
            detail="No source columns available for mapping"
        )

    # =========================================
    # 🔹 TARGET
    # =========================================
    eba_template = db.query(EbaTemplate).filter(
        EbaTemplate.name == target_ws,
        EbaTemplate.workflow_id == workflow_id
    ).first()

    if not eba_template:
        raise HTTPException(status_code=404, detail="Target worksheet not found")

    target_columns = (eba_template.structure or {}).get("columns", [])

    if not target_columns:
        raise HTTPException(
            status_code=400,
            detail="No target columns available for mapping"
        )

    # =========================================
    # 🔥 AGENT EXECUTION (SAFE)
    # =========================================
    try:


        generated_mapping = run_hybrid_mapping_agent(
            source_columns,
            target_columns,
            source_ws,
            target_ws,
            db,
            workflow_id=workflow_id
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Mapping agent failed: {str(e)}"
        )

    # =========================================
    # 🔥 VALIDATE AGENT OUTPUT STRUCTURE
    # =========================================
    if not isinstance(generated_mapping, list):
        raise HTTPException(
            status_code=500,
            detail="Invalid mapping response from agent"
        )

    if not generated_mapping:
        raise HTTPException(
            status_code=400,
            detail="Agent returned empty mapping"
        )

    # =========================================
    # 🔹 VALIDATION (EXISTING)
    # =========================================
    validate_mapping_request(
        generated_mapping,
        source_columns,
        target_columns,
        source_ws,
        target_ws
    )

    # =========================================
    # 🔹 SAVE
    # =========================================
    saved_mapping = save_or_update_mapping(
        db,
        workflow_id,
        source_ws,
        target_ws,
        generated_mapping
    )

    # =========================================
    # 🔹 STORE HISTORY (SAFE)
    # =========================================
    try:
        store_mapping_history(saved_mapping.mapping)
    except Exception as e:
        # 🔥 DO NOT FAIL API (important design)
        print("Pinecone storage failed:", str(e))

    # =========================================
    # 🔹 RESPONSE
    # =========================================
    return {
        "status": "success",
        "data": {
            "mapping": saved_mapping.mapping,
            "count": len(saved_mapping.mapping)
        },
        "error": None,
        "meta": {
            "request_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat()
        }
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

@router.post("/mapping-feedback")
def capture_feedback(
    payload: dict,
    db: Session = Depends(get_db)
):
    return save_feedback(
        db=db,
        workflow_id=payload["workflow_id"],
        source_field=payload["source_field"],
        suggested_field=payload.get("suggested_field"),
        final_field=payload["final_field"],
        action=payload["action"]
    )