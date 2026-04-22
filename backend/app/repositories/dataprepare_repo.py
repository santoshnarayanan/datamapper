"""
Execution Logs Handling

Purpose:
--------
Execution logs track the outcome of each step during workflow execution.

They are used for:
1. Debugging failures (which step failed and why)
2. Replay validation (ensuring deterministic behavior)
3. Observability (future monitoring dashboards)

Structure:
----------
Each log entry contains:
- step index
- status (SUCCESS / FAILED)
- error message (if failed)
- retry attempts (future extension)

IMPORTANT DESIGN RULE:
----------------------
- Logs must reflect EXACT execution order
- Logs must NOT be modified during replay
- Logs are append-only per execution

Why critical:
-------------
These logs are the only source of truth for:
- Failure diagnosis
- Replay correctness
"""



from app.models.dataprepare import DataPrepare
from sqlalchemy.orm import Session
from app.models import DataPrepare

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
        DataPrepare.worksheet_id == worksheet_id,
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