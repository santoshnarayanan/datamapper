from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.worksheet import Worksheet
from app.services.dataprepare_service import (
    delete_column, remove_rows, make_first_row_header
)

from app.repositories.dataprepare_repo import save_dataprepare_step

from app.repositories.dataprepare_repo import (
    get_dataprepare, save_or_update_steps
)
from app.services.dataprepare_service import replay_steps

router = APIRouter()


@router.post("/dataprepare")
def apply_transformation(
        workflow_id: str,
        worksheet_id: str,
        action: str,
        payload: dict,
        db: Session = Depends(get_db)
):
    # Step 1: Load worksheet (ORIGINAL DATA)
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

    # Step 4: Replay ALL steps
    updated_data = replay_steps(original_data, steps)

    # Step 5: Save steps
    save_or_update_steps(db, workflow_id, worksheet_id, steps)

    # Step 6: Save computed data
    worksheet.data = updated_data
    db.commit()

    return {
        "columns": updated_data["columns"],
        "rows": updated_data["rows"][:50],
        "steps_count": len(steps)
    }


@router.post("/dataprepare/undo")
def undo_last_step(
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

    steps = dp.steps[:-1]  # remove last step

    # Replay remaining steps
    original_data = worksheet.data
    updated_data = replay_steps(original_data, steps)

    # Save updated steps
    save_or_update_steps(db, workflow_id, worksheet_id, steps)

    # Save data
    worksheet.data = updated_data
    db.commit()

    return {
        "columns": updated_data["columns"],
        "rows": updated_data["rows"][:50],
        "steps_count": len(steps)
    }