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

with workflow.unsafe.imports_passed_through():
    from app.temporal.activities import apply_step_activity


@workflow.defn
class DataPreparationWorkflow:

    @workflow.run
    async def run(self, steps: list, data: list):

        current_data = data
        execution_logs = []

        for idx, step in enumerate(steps):
            try:
                current_data = await workflow.execute_activity(
                    apply_step_activity,
                    step,
                    current_data,
                    start_to_close_timeout=timedelta(seconds=10),
                    retry_policy={
                        "maximum_attempts": 3,
                        "initial_interval": timedelta(seconds=1),
                        "backoff_coefficient": 2.0,
                    },
                )

                # Execution logs capture step-by-step workflow behavior.
                # These logs are critical for debugging and replay validation.
                #
                # Design Notes:
                # - Maintains strict execution order
                # - Stops logging after failure
                # - Used later for observability (Phase 6.3)

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

                # Stop execution on failure
                return {
                    "status": "FAILED",
                    "failed_step": idx,
                    "logs": execution_logs
                }

        return {
            "status": "SUCCESS",
            "data": current_data,
            "logs": execution_logs
        }