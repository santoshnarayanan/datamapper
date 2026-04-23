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

router = APIRouter()


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

    handle = await client.start_workflow(
        DataPreparationWorkflow.run,
        args=[payload["steps"], normalize_data(payload["data"])],
        id=f"workflow-{payload['workflow_id']}",
        task_queue="data-prepare-queue",
    )

    result = await handle.result()

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

        handle = await client.start_workflow(
            DataPreparationWorkflow.run,
            args=[remaining_steps, base_data],
            id=temporal_workflow_id,
            task_queue="data-prepare-queue",
        )

        result = await handle.result()

        # ===============================
        # Save execution logs
        # ===============================
        from datetime import datetime

        dp.execution_logs = dp.execution_logs or []

        dp.execution_logs.append({
            "run_id": temporal_workflow_id,
            "timestamp": datetime.utcnow().isoformat(),
            "execution_log": result.get("logs", []),
            "status": result.get("status"),
            "type": "apply"
        })

        flag_modified(dp, "execution_logs")
        db.add(dp)

        if result["status"] == "FAILED":
            db.commit()
            return {
                "error": result.get("error"),
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

        return {
            "columns": updated_data["columns"],
            "rows": updated_data["rows"][:50],
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

    handle = await client.start_workflow(
        DataPreparationWorkflow.run,
        args=[steps, original_data],
        task_queue="data-prepare-queue",
        id=temporal_workflow_id,
    )

    result = await handle.result()

    # Save execution logs
    from datetime import datetime
    from sqlalchemy.orm.attributes import flag_modified

    dp.execution_logs = dp.execution_logs or []

    dp.execution_logs.append({
        "run_id": temporal_workflow_id,
        "timestamp": datetime.utcnow().isoformat(),
        "execution_log": result.get("logs", []),
        "status": result.get("status"),
        "type": "undo"
    })

    flag_modified(dp, "execution_logs")
    db.add(dp)

    if result["status"] == "FAILED":
        db.commit()
        return {
            "error": result.get("error"),
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

    return {
        "columns": updated_data["columns"],
        "rows": updated_data["rows"][:50],
        "steps_count": len(steps)
    }