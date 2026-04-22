from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.excel_service import parse_excel

# 🔥 UPDATED IMPORTS
from app.repositories.worksheet_repo import create_new_version
from app.repositories.dataprepare_repo import get_previous_steps
from app.services.replay_service import trigger_replay

router = APIRouter()


@router.post("/upload")
async def upload_excel(
    file: UploadFile = File(...),
    workflow_id: str = Form(...),
    db: Session = Depends(get_db)
):
    # Step 1: Parse Excel
    parsed_data = parse_excel(file.file)

    # Step 2: Create new version
    worksheet = create_new_version(
        db=db,
        workflow_id=workflow_id,
        name=file.filename,
        data=parsed_data
    )

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

    # Step 5: Response
    return {
        "worksheet_id": str(worksheet.id),
        "version": worksheet.version,
        "columns": parsed_data["columns"],
        "rows": parsed_data["rows"][:50],
        "replay_triggered": bool(steps)
    }