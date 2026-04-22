from temporalio.client import Client


from app.services.dataprepare_service import handle_replay_result
from app.core.database import SessionLocal

from app.temporal.workflows import DataPreparationWorkflow

# ===============================
# 🔥 NORMALIZE DATA (CRITICAL)
# ===============================
def normalize_data(data):
    """
    Ensures data is always:
    { columns: [...], rows: [...] }
    """
    if isinstance(data, list):
        return {
            "columns": list(data[0].keys()) if data else [],
            "rows": data
        }
    return data

async def trigger_replay(workflow_id, worksheet_id, steps, data):

    client = await Client.connect("localhost:7233")

    handle = await client.start_workflow(
        DataPreparationWorkflow.run,
        args=[steps, normalize_data(data)],
        id=f"replay-{workflow_id}-{worksheet_id}",
        task_queue="data-prepare-queue",
    )

    # 🔥 WAIT for result
    result = await handle.result()

    # 🔥 SAVE RESULT
    db = SessionLocal()
    try:
        response = handle_replay_result(
            db,
            workflow_id,
            worksheet_id,
            result
        )
    finally:
        db.close()

    return response