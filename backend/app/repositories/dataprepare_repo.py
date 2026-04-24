
from sqlalchemy.orm import Session
from app.models import DataPrepare
from app.models.worksheet import Worksheet


def save_dataprepare_step(db, workflow_id, worksheet_id, step):
    dp = DataPrepare(
        workflow_id=workflow_id,
        worksheet_id=worksheet_id,
        steps=[step]  # simple for now
    )

    db.add(dp)
    db.commit()
    db.refresh(dp)

    return dp


def get_dataprepare(db, workflow_id, worksheet_id):
    return db.query(DataPrepare).filter(
        DataPrepare.workflow_id == workflow_id,
        DataPrepare.worksheet_id == worksheet_id
    ).first()


def save_or_update_steps(db, workflow_id, worksheet_id, steps):
    dp = get_dataprepare(db, workflow_id, worksheet_id)

    if dp:
        dp.steps = steps
    else:
        dp = DataPrepare(
            workflow_id=workflow_id,
            worksheet_id=worksheet_id,
            steps=steps
        )
        db.add(dp)

    db.commit()
    db.refresh(dp)

    return dp

def save_snapshot(db, dp, step_number, data):
    snapshots = dp.snapshots or {}

    snapshots[str(step_number)] = data

    dp.snapshots = snapshots
    # ensure the SQLALchemy detects change
    db.add(dp)
    db.refresh(dp)

    return dp


def update_execution_logs(
    db: Session,
    workflow_id: str,
    worksheet_id: str,
    logs: list
):
    record = db.query(DataPrepare).filter_by(
        workflow_id=workflow_id,
        worksheet_id=worksheet_id
    ).first()

    if record:
        record.execution_logs = logs
        db.commit()


def get_previous_steps(db, workflow_id, worksheet_name):
    """
    Fetch steps from latest version of worksheet
    """
    dp = db.query(DataPrepare).join(
        Worksheet,
        DataPrepare.worksheet_id == Worksheet.id
    ).filter(
        DataPrepare.workflow_id == workflow_id,
        Worksheet.name == worksheet_name
    ).order_by(Worksheet.version.desc()).first()

    return dp.steps if dp else []