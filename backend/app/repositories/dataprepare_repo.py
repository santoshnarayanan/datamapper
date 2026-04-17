from app.models.dataprepare import DataPrepare


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
