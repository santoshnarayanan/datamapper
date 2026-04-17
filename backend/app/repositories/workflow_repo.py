from app.models.workflow import Workflow

def create_workflow(db, user_email):
    workflow = Workflow(user_email=user_email)

    db.add(workflow)
    db.commit()
    db.refresh(workflow)

    return workflow