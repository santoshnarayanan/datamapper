from app.models.worksheet import Worksheet
from sqlalchemy.orm import Session


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


def create_new_version(db: Session, workflow_id: str, name: str, data: dict):
    """
    Create new version of worksheet
    """

    latest = db.query(Worksheet).filter_by(
        workflow_id=workflow_id,
        name=name
    ).order_by(Worksheet.version.desc()).first()

    new_version = 1 if not latest else latest.version + 1

    worksheet = Worksheet(
        workflow_id=workflow_id,
        name=name,
        data=data,
        version=new_version
    )

    db.add(worksheet)
    db.commit()
    db.refresh(worksheet)

    return worksheet