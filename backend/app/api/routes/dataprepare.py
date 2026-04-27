from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from temporalio.client import Client
import uuid

from app.core.database import get_db
from app.models.worksheet import Worksheet

from app.repositories.dataprepare_repo import (
    get_dataprepare, save_or_update_steps
)

from app.temporal.workflows import DataPreparationWorkflow
from app.core.error_classifier import classify_error


router = APIRouter()

# ===============================
# 🔥 HELPER FUNCTION FOR PAGINATION
# ===============================

def paginate_rows(rows, page, page_size):
    start = (page - 1) * page_size
    end = start + page_size
    return rows[start:end]

# ===============================
# 🔥 NORMALIZE DATA (CRITICAL FIX)
# ===============================
def normalize_data(data):
    """
    Ensures data is always in:
    { columns: [...], rows: [...] }
    """
    if isinstance(data, list):
        return {
            "columns": list(data[0].keys()) if data else [],
            "rows": data
        }
    return data


# ===============================
# RUN DATA PREPARE (TEST ENDPOINT)
# ===============================
@router.post("/run-data-prepare")
async def run_data_prepare(payload: dict):

    client = await Client.connect("localhost:7233")

    start_time = datetime.utcnow()
    handle = await client.start_workflow(
        DataPreparationWorkflow.run,
        args=[payload["steps"], normalize_data(payload["data"])],
        id=f"workflow-{payload['workflow_id']}",
        task_queue="data-prepare-queue",
    )

    result = await handle.result()

    end_time = datetime.utcnow()
    duration_ms = int((end_time - start_time).total_seconds() * 1000)

    return result


# ===============================
# APPLY TRANSFORMATION
# ===============================
@router.post("/dataprepare")
async def apply_transformation(
    workflow_id: str,
    worksheet_id: str,
    action: str,
    payload: dict,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db)
):
    worksheet = db.query(Worksheet).filter(
        Worksheet.id == worksheet_id
    ).first()

    if not worksheet:
        return {"error": "Worksheet not found"}

    try:
        dp = get_dataprepare(db, workflow_id, worksheet_id)

        # Ensure dp exists
        if not dp:
            save_or_update_steps(db, workflow_id, worksheet_id, [])
            db.commit()
            dp = get_dataprepare(db, workflow_id, worksheet_id)

        steps = list(dp.steps) if dp and dp.steps else []

        new_step = {
            "operation": action,
            **payload
        }

        temp_steps = steps + [new_step]

        dp = get_dataprepare(db, workflow_id, worksheet_id)
        snapshots = dp.snapshots or {}

        from sqlalchemy.orm.attributes import flag_modified

        # ===============================
        # Initialize snapshot (normalized)
        # ===============================
        if not snapshots:
            dp.snapshots = {
                "0": normalize_data(worksheet.data)
            }
            flag_modified(dp, "snapshots")
            db.add(dp)
            db.commit()

            dp = get_dataprepare(db, workflow_id, worksheet_id)
            snapshots = dp.snapshots or {}

        last_step = max([int(k) for k in snapshots.keys()], default=0)

        if last_step > 0:
            base_data = normalize_data(snapshots[str(last_step)])
        else:
            base_data = worksheet.data

        # 🔥 NORMALIZE HERE (CRITICAL)
        base_data = normalize_data(base_data)

        remaining_steps = temp_steps[last_step:]

        client = await Client.connect("localhost:7233")

        temporal_workflow_id = f"dp-{uuid.uuid4()}"

        start_time = datetime.utcnow()
        handle = await client.start_workflow(
            DataPreparationWorkflow.run,
            args=[remaining_steps, base_data],
            id=temporal_workflow_id,
            task_queue="data-prepare-queue",
        )

        result = await handle.result()

        end_time = datetime.utcnow()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)


        # ===============================
        # Save execution logs
        # ===============================

        dp.execution_logs = dp.execution_logs or []

        dp.execution_logs.append({
            "run_id": temporal_workflow_id,
            "type": "apply",
            "status": result.get("status"),
            "error_type": classify_error(result.get("error")) if result.get("status") == "FAILED" else None,
            "started_at": start_time.isoformat(),
            "completed_at": end_time.isoformat(),
            "duration_ms": duration_ms,
            "steps": result.get("logs", [])
        })

        flag_modified(dp, "execution_logs")
        db.add(dp)

        if result["status"] == "FAILED":
            db.commit()

            error_message = result.get("error")
            error_type = classify_error(error_message)

            return {
                "error": error_message,
                "error_type": error_type,  # ✅ ADD THIS
                "failed_step": result.get("failed_step"),
                "execution_log": result.get("logs")
            }

        updated_data = result["data"]

        # Save steps only after success
        save_or_update_steps(db, workflow_id, worksheet_id, temp_steps)

        dp.snapshots = dp.snapshots or {}
        dp.snapshots[str(len(temp_steps))] = normalize_data(updated_data)

        flag_modified(dp, "snapshots")
        db.add(dp)

        # worksheet.data = normalize_data(updated_data)
        db.commit()

        rows = updated_data.get("rows", [])
        total = len(rows)

        return {
            "columns": updated_data.get("columns", []),
            "rows": paginate_rows(rows, page, page_size),
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size
            },
            "steps_count": len(temp_steps)
        }

    except Exception as e:
        db.rollback()
        return {
            "error": str(e),
            "message": "DataPrepare execution failed"
        }


# ===============================
# UNDO LAST STEP
# ===============================
@router.post("/dataprepare/undo")
async def undo_last_step(
    workflow_id: str,
    worksheet_id: str,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db)
):
    worksheet = db.query(Worksheet).filter(
        Worksheet.id == worksheet_id
    ).first()

    if not worksheet:
        return {"error": "Worksheet not found"}

    dp = get_dataprepare(db, workflow_id, worksheet_id)

    if not dp or not dp.steps:
        return {"error": "No steps to undo"}

    steps = dp.steps[:-1]

    snapshots = dp.snapshots or {}

    # 🔥 NORMALIZE HERE
    original_data = normalize_data(
        snapshots.get("0", worksheet.data)
    )

    # Clean snapshots after undo
    valid_keys = set(str(i) for i in range(len(steps) + 1))
    dp.snapshots = {
        k: v for k, v in snapshots.items() if k in valid_keys
    }

    client = await Client.connect("localhost:7233")

    temporal_workflow_id = f"undo-{uuid.uuid4()}"

    start_time = datetime.utcnow()
    handle = await client.start_workflow(
        DataPreparationWorkflow.run,
        args=[steps, original_data],
        task_queue="data-prepare-queue",
        id=temporal_workflow_id,
    )

    result = await handle.result()

    end_time = datetime.utcnow()
    duration_ms = int((end_time - start_time).total_seconds() * 1000)


    # Save execution logs
    from sqlalchemy.orm.attributes import flag_modified

    dp.execution_logs = dp.execution_logs or []


    dp.execution_logs.append({
        "run_id": temporal_workflow_id,
        "type": "undo",
        "status": result.get("status"),
        "error_type": classify_error(result.get("error")) if result.get("status") == "FAILED" else None,
        "started_at": start_time.isoformat(),
        "completed_at": end_time.isoformat(),
        "duration_ms": duration_ms,
        "steps": result.get("logs", [])
    })

    flag_modified(dp, "execution_logs")
    db.add(dp)

    if result["status"] == "FAILED":
        db.commit()

        error_message = result.get("error")
        error_type = classify_error(error_message)

        return {
            "error": error_message,
            "error_type": error_type,  # ✅ ADD THIS
            "failed_step": result.get("failed_step"),
            "execution_log": result.get("logs")
        }

    updated_data = result["data"]

    dp.snapshots = dp.snapshots or {}
    dp.snapshots[str(len(steps))] = normalize_data(updated_data)

    flag_modified(dp, "snapshots")
    db.add(dp)

    save_or_update_steps(db, workflow_id, worksheet_id, steps)

    # worksheet.data = normalize_data(updated_data)
    db.commit()

    rows = updated_data.get("rows", [])
    total = len(rows)

    return {
        "columns": updated_data.get("columns", []),
        "rows": paginate_rows(rows, page, page_size),
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size
        },
        "steps_count": len(steps)
    }