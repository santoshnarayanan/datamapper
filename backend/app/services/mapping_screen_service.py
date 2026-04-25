from sqlalchemy.orm import Session
from app.models.worksheet import Worksheet
from app.models.ebatemplate import EbaTemplate


def get_latest_worksheet(db: Session, workflow_id: str, worksheet_name: str):
    return db.query(Worksheet).filter(
        Worksheet.workflow_id == workflow_id,
        Worksheet.name == worksheet_name
    ).order_by(Worksheet.version.desc()).first()


def get_all_source_worksheets(db: Session, workflow_id: str):
    worksheets = db.query(Worksheet).filter(
        Worksheet.workflow_id == workflow_id
    ).all()

    return list(set([w.name for w in worksheets]))


def get_all_target_templates(db: Session):
    templates = db.query(EbaTemplate).all()
    return [t.name for t in templates]


def get_target_template(db: Session, target_ws: str):
    return db.query(EbaTemplate).filter(
        EbaTemplate.name == target_ws
    ).first()