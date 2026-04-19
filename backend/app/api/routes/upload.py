from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.excel_service import parse_excel
from app.repositories.worksheet_repo import create_worksheet

router = APIRouter()


@router.post("/upload")
async def upload_excel(
    file: UploadFile = File(...),
    workflow_id: str = Form(...),   # ✅ comes from request
    db: Session = Depends(get_db)
):
    # Step 1: Parse Excel
    parsed_data = parse_excel(file.file)

    # Step 2: Save worksheet (FIX HERE)
    worksheet = create_worksheet(
        db=db,
        workflow_id=workflow_id,   # ✅ CORRECT VALUE
        name=file.filename,
        data=parsed_data
    )

    # Step 3: Return response
    return {
        "worksheet_id": str(worksheet.id),   # renamed for clarity
        "columns": parsed_data["columns"],
        "rows": parsed_data["rows"][:50]
    }