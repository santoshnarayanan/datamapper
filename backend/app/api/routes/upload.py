from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.excel_service import parse_excel

# 🔥 UPDATED IMPORTS
from app.repositories.worksheet_repo import create_new_version
from app.repositories.dataprepare_repo import get_previous_steps
from app.services.replay_service import trigger_replay
from app.repositories.worksheet_row_repo import bulk_insert_rows

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

# TODO improve Upload to handle multiple worksheets
@router.post("/upload")
async def upload_excel(
    file: UploadFile = File(...),
    workflow_id: str = Form(...),
    db: Session = Depends(get_db)
):
    # Step 1: Parse Excel
    parsed_data = normalize_data(parse_excel(file.file))


    # Step 2: Create new version
    worksheet = create_new_version(
        db=db,
        workflow_id=workflow_id,
        name=file.filename,
        data=parsed_data
    )

    bulk_insert_rows(db, worksheet.id, parsed_data["rows"])

    # Step 3: Fetch previous steps
    steps = get_previous_steps(
        db=db,
        workflow_id=workflow_id,
        worksheet_name=file.filename
    )

    # Step 4: Auto replay if steps exist
    if steps:
        await trigger_replay(
            workflow_id=workflow_id,
            worksheet_id=str(worksheet.id),
            steps=steps,
            data=parsed_data
        )
    # TODO UI is limited to 50 rows
    # Step 5: Response
    return {
        "worksheet_id": str(worksheet.id),
        "version": worksheet.version,
        "columns": parsed_data["columns"],
        "rows": parsed_data["rows"][:50],
        "replay_triggered": bool(steps)
    }