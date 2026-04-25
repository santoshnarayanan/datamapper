from app.models import DataPrepare
from uuid import UUID

def delete_column(data, column_name):
    columns = data["columns"]
    rows = data["rows"]

    if column_name not in columns:
        return data

    columns.remove(column_name)

    for row in rows:
        row.pop(column_name, None)

    return {"columns": columns, "rows": rows}


def remove_rows(data, row_indices):
    rows = data["rows"]

    new_rows = [
        row for i, row in enumerate(rows)
        if i not in row_indices
    ]

    return {
        "columns": data["columns"],
        "rows": new_rows
    }


def make_first_row_header(data):
    rows = data["rows"]

    if not rows:
        return data

    new_columns = list(rows[0].values())
    new_rows = rows[1:]

    return {
        "columns": new_columns,
        "rows": new_rows
    }

def apply_step(data, step):
    action = step["action"]
    payload = step["payload"]

    if action == "delete_column":
        return delete_column(data, payload["column"])

    elif action == "remove_rows":
        return remove_rows(data, payload["rows"])

    elif action == "make_header":
        return make_first_row_header(data)

    return data


def replay_steps(original_data, steps):
    data = original_data

    for step in steps:
        data = apply_step(data, step)

    return data

def handle_replay_result(db, workflow_id, worksheet_id, result):
    """
    Save replay result safely
    """

    if result["status"] == "SUCCESS":

        dp = DataPrepare(
            workflow_id=workflow_id,
            worksheet_id=worksheet_id,
            steps=result.get("steps", []),
            snapshots=result.get("snapshots", {}),
            execution_logs=result.get("logs", [])
        )

        db.add(dp)
        db.commit()
        db.refresh(dp)

        return {"status": "saved"}

    else:
        # 🔥 CRITICAL RULE
        # Do NOT overwrite previous successful state

        return {
            "status": "failed",
            "reason": "Replay failed — previous version preserved"
        }

def get_latest_dataprepare_snapshot(db, workflow_id: str, worksheet_id: str):
    """
    Fetch latest dataprepare snapshot for given workflow and worksheet
    """

    try:
        workflow_id = UUID(workflow_id)
    except:
        return None

    record = db.query(DataPrepare).filter(
        DataPrepare.workflow_id == workflow_id,
        DataPrepare.worksheet_id == worksheet_id
    ).order_by(DataPrepare.updated_at.desc()).first()

    if not record:
        return None

    snapshots = record.snapshots or {}

    if not snapshots or not isinstance(snapshots, dict):
        return None

    last_key = max(snapshots.keys(), key=int)
    return snapshots[last_key]