from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from temporalio.client import Client
import uuid

from app.core.database import get_db
from app.models.worksheet import Worksheet

from app.repositories.dataprepare_repo import (
    get_dataprepare, save_or_update_steps
)

from temporal_worker.workflows import DataPrepareWorkflow

router = APIRouter()


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
    # Step 1: Load worksheet
    worksheet = db.query(Worksheet).filter(
        Worksheet.id == worksheet_id
    ).first()

    if not worksheet:
        return {"error": "Worksheet not found"}

    original_data = worksheet.data

    # Step 2: Get existing steps
    dp = get_dataprepare(db, workflow_id, worksheet_id)
    steps = dp.steps if dp and dp.steps else []

    # Step 3: Append new step
    new_step = {
        "action": action,
        "payload": payload
    }
    steps.append(new_step)

    # 🚀 Step 4: Call Temporal Workflow (FIXED)
    client = await Client.connect("localhost:7233")

    temporal_workflow_id = f"dp-{uuid.uuid4()}"

    handle = await client.start_workflow(
        DataPrepareWorkflow.run,
        {
            "data": original_data,
            "steps": steps
        },   # ✅ SINGLE INPUT (DICT)
        id=temporal_workflow_id,
        task_queue="hello-task-queue",
    )

    updated_data = await handle.result()

    # Step 5: Save steps
    save_or_update_steps(db, workflow_id, worksheet_id, steps)

    # Step 6: Save updated data
    worksheet.data = updated_data
    db.commit()

    return {
        "columns": updated_data["columns"],
        "rows": updated_data["rows"][:50],
        "steps_count": len(steps)
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

    # Step 1: Remove last step
    steps = dp.steps[:-1]

    original_data = worksheet.data

    # 🚀 Step 2: Call Temporal Workflow (FIXED)
    client = await Client.connect("localhost:7233")

    temporal_workflow_id = f"undo-{uuid.uuid4()}"

    handle = await client.start_workflow(
        DataPrepareWorkflow.run,
        {
            "data": original_data,
            "steps": steps
        },   # ✅ SINGLE INPUT (DICT)
        id=temporal_workflow_id,
        task_queue="hello-task-queue",
    )

    updated_data = await handle.result()

    # Step 3: Save updated steps
    save_or_update_steps(db, workflow_id, worksheet_id, steps)

    # Step 4: Save updated data
    worksheet.data = updated_data
    db.commit()

    return {
        "columns": updated_data["columns"],
        "rows": updated_data["rows"][:50],
        "steps_count": len(steps)
    }