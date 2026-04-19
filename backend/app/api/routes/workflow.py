import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.workflow_repo import create_workflow

from temporalio.client import Client

from temporal_worker.workflows import HelloWorkflow

router = APIRouter()


@router.post("/workflow")
def create_new_workflow(user_email: str, db: Session = Depends(get_db)):
    workflow = create_workflow(db, user_email)

    return {
        "workflow_id": str(workflow.id),
        "user_email": workflow.user_email
    }

@router.get("/temporal-test")
async def temporal_test():
    client = await Client.connect("localhost:7233")

    workflow_id = f"test-{uuid.uuid4()}"  # Create unique ID

    handle = await client.start_workflow(
        HelloWorkflow.run,
        "Santosh",
        id=workflow_id,
        task_queue="hello-task-queue",
    )

    result = await handle.result()

    return {"result": result}