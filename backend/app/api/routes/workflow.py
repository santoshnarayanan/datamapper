from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.workflow_repo import create_workflow


router = APIRouter()


@router.post("/workflow")
def create_new_workflow(user_email: str, db: Session = Depends(get_db)):
    workflow = create_workflow(db, user_email)

    return {
        "workflow_id": str(workflow.id),
        "user_email": workflow.user_email
    }
