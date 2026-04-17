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
