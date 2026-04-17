from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.worksheet import Worksheet
from app.services.dataprepare_service import (
    delete_column, remove_rows, make_first_row_header
)

from app.repositories.dataprepare_repo import save_dataprepare_step

router = APIRouter()


@router.post("/dataprepare")
def apply_transformation(workflow_id: str, worksheet_id: str, action: str, payload: dict, db: Session = Depends(get_db)):
    # Step 1 : Load worksheet
    worksheet = db.query(Worksheet).filter(Worksheet.id == worksheet_id).first()

    if not worksheet:
        return {"error": "Worksheet not found"}

    data = worksheet.data

    # Step 2 : Apply transformation

    if action == "delete_column":
        data = delete_column(data, payload["columns"])

    elif action == "remove_rows":
        data = remove_rows(data, payload["rows"])

    elif action == "make_header":
        data = make_first_row_header(data)

    else:
            return{"error": "Action not recognized"}

    # Step 3 Save updated worksheet

    worksheet.data = data
    db.commit()

    # Step 4 Save Step


    # Step 4: Save step
    save_dataprepare_step(
        db,
        workflow_id,
        worksheet_id,
        {
            "action": action,
            "payload": payload
        }
    )

    return {
        "columns": data["columns"],
        "rows": data["rows"][:50]
    }