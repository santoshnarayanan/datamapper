"""
DataPreparationWorkflow

This workflow:
--------------
- Executes steps sequentially
- Applies retry policy via activities
- Tracks execution logs

CRITICAL BEHAVIOR:
------------------
1. Steps execute in order
2. On failure → workflow stops
3. Failed steps are NOT persisted (Phase 5.5 rule)

WHY STOP ON FAILURE?
--------------------
To preserve:
✔ Determinism
✔ Replay integrity
✔ Data correctness
"""


from temporalio import workflow
from datetime import timedelta
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from app.temporal.activities import apply_step_activity


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


@workflow.defn
class DataPreparationWorkflow:

    @workflow.run
    async def run(self, steps: list, data: dict):

        # 🔥 CRITICAL FIX: normalize input
        current_data = normalize_data(data)

        execution_logs = []

        for idx, step in enumerate(steps):
            try:
                # 🔥 CRITICAL FIX: normalize before every step
                current_data = normalize_data(current_data)

                current_data = await workflow.execute_activity(
                    apply_step_activity,
                    args=[step, current_data],
                    start_to_close_timeout=timedelta(seconds=10),
                    retry_policy=RetryPolicy(
                        maximum_attempts=3,
                        initial_interval=timedelta(seconds=1),
                        backoff_coefficient=2.0,
                    ),
                )

                execution_logs.append({
                    "step": idx,
                    "status": "SUCCESS"
                })

            except Exception as e:
                execution_logs.append({
                    "step": idx,
                    "status": "FAILED",
                    "error": str(e)
                })

                return {
                    "status": "FAILED",
                    "failed_step": idx,
                    "error": str(e),
                    "logs": execution_logs
                }

        return {
            "status": "SUCCESS",
            "data": current_data,
            "steps": steps,
            "snapshots": {},
            "logs": execution_logs
        }