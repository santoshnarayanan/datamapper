from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from temporalio.client import Client
import uuid

from app.core.database import get_db
from app.models.worksheet import Worksheet

from app.repositories.dataprepare_repo import (
    get_dataprepare, save_or_update_steps, save_snapshot
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
    worksheet = db.query(Worksheet).filter(
        Worksheet.id == worksheet_id
    ).first()

    if not worksheet:
        return {"error": "Worksheet not found"}

    try:
        dp = get_dataprepare(db, workflow_id, worksheet_id)

        # 🔥 FIX: Ensure dp exists
        if not dp:
            save_or_update_steps(db, workflow_id, worksheet_id, [])
            db.commit()
            dp = get_dataprepare(db, workflow_id, worksheet_id)

        steps = list(dp.steps) if dp and dp.steps else []

        new_step = {
            "action": action,
            "payload": payload
        }

        temp_steps = steps + [new_step]

        dp = get_dataprepare(db, workflow_id, worksheet_id)
        snapshots = dp.snapshots or {}

        from sqlalchemy.orm.attributes import flag_modified

        if not snapshots:
            dp.snapshots = {
                "0": worksheet.data
            }
            flag_modified(dp, "snapshots")
            db.add(dp)
            db.commit()

            dp = get_dataprepare(db, workflow_id, worksheet_id)
            snapshots = dp.snapshots or {}

        last_step = max([int(k) for k in snapshots.keys()], default=0)

        if last_step > 0:
            base_data = snapshots[str(last_step)]
        else:
            base_data = worksheet.data

        remaining_steps = temp_steps[last_step:]

        client = await Client.connect("localhost:7233")

        temporal_workflow_id = f"dp-{uuid.uuid4()}"

        handle = await client.start_workflow(
            DataPrepareWorkflow.run,
            {
                "data": base_data,
                "steps": remaining_steps
            },
            id=temporal_workflow_id,
            task_queue="hello-task-queue",
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
            "execution_log": result.get("execution_log", []),
            "status": result.get("status"),
            "type": "apply"
        })

        flag_modified(dp, "execution_logs")
        db.add(dp)

        if result["status"] == "failed":
            db.commit()
            return {
                "error": result["error"],
                "failed_step": result["failed_step"],
                "execution_log": result["execution_log"]
            }

        updated_data = result["data"]

        # 🔥 SAVE STEPS ONLY AFTER SUCCESS
        save_or_update_steps(db, workflow_id, worksheet_id, temp_steps)

        dp.snapshots = dp.snapshots or {}
        dp.snapshots[str(len(temp_steps))] = updated_data

        flag_modified(dp, "snapshots")
        db.add(dp)

        worksheet.data = updated_data
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
    original_data = snapshots.get("0", worksheet.data)

    # 🔥 FIX 2: clean snapshots after undo
    valid_keys = set(str(i) for i in range(len(steps) + 1))
    dp.snapshots = {
        k: v for k, v in snapshots.items() if k in valid_keys
    }

    client = await Client.connect("localhost:7233")

    temporal_workflow_id = f"undo-{uuid.uuid4()}"

    handle = await client.start_workflow(
        DataPrepareWorkflow.run,
        {
            "data": original_data,
            "steps": steps
        },
        id=temporal_workflow_id,
        task_queue="hello-task-queue",
    )

    result = await handle.result()

    # ===============================
    # Step 5.4: Save execution logs (UNDO)
    # ===============================
    from datetime import datetime
    from sqlalchemy.orm.attributes import flag_modified

    dp.execution_logs = dp.execution_logs or []

    dp.execution_logs.append({
        "run_id": temporal_workflow_id,
        "timestamp": datetime.utcnow().isoformat(),
        "execution_log": result.get("execution_log", []),
        "status": result.get("status"),
        "type": "undo"
    })

    flag_modified(dp, "execution_logs")
    db.add(dp)

    if result["status"] == "failed":
        db.commit()
        return {
            "error": result["error"],
            "failed_step": result["failed_step"],
            "execution_log": result["execution_log"]
        }

    updated_data = result["data"]

    dp.snapshots = dp.snapshots or {}
    dp.snapshots[str(len(steps))] = updated_data

    flag_modified(dp, "snapshots")
    db.add(dp)

    save_or_update_steps(db, workflow_id, worksheet_id, steps)

    worksheet.data = updated_data
    db.commit()

    return {
        "columns": updated_data["columns"],
        "rows": updated_data["rows"][:50],
        "steps_count": len(steps)
    }