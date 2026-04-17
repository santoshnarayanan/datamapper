from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session

from app.api.routes import workflow
from app.core.database import get_db
from app.services.excel_service import  parse_excel
from app.repositories.worksheet_repo import create_worksheet

router = APIRouter()

@router.post("/upload")
async def upload_excel(file: UploadFile = File(...), workflow_id: str = Form(...),db: Session = Depends(get_db)):

    parsed_data = parse_excel(file.file)
    worksheet = create_worksheet(db=db, workflow_id=workflow,name=file.filename,data=parsed_data)

    return {
        # Step 1: Parsed excel
        "worksheet": str(worksheet.id),

        # Step 2: Save to DB
        "columns": parsed_data["columns"],

        # Step 3:  Return preview
        "rows": parsed_data["rows"][:50]
    }