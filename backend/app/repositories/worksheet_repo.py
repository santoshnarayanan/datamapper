from app.models.worksheet import Worksheet


def create_worksheet(db, workflow_id, name, data):
    worksheet = Worksheet(
        workflow_id=workflow_id,
        name=name,
        data=data
    )

    db.add(worksheet)
    db.commit()
    db.refresh(worksheet)   # ✅ important

    return worksheet        # ✅ MUST return