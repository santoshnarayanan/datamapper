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

from temporalio import workflow
from datetime import timedelta
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from app.temporal.activities import apply_step_activity


@workflow.defn
class DataPreparationWorkflow:

    @workflow.run
    async def run(self, steps: list, data: dict):
        current_data = data
        execution_logs = []

        for idx, step in enumerate(steps):

            try:
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
                    "status": "SUCCESS",
                    "attempts": 1  # Temporal retries hidden, we approximate
                })


            except Exception as e:
                error_message = str(e)

                # 🔥 Extract underlying cause safely
                cause = getattr(e, "cause", None)
                if cause:
                    error_message = str(cause)

                # 🔥 Remove extra quotes cleanly
                if error_message.startswith('"') and error_message.endswith('"'):
                    error_message = error_message[1:-1]

                execution_logs.append({

                    "step": idx,
                    "status": "FAILED",
                    "error": error_message,
                    "attempts": 3

                })

                return {

                    "status": "FAILED",
                    "failed_step": idx,
                    "error": error_message,
                    "logs": execution_logs

                }

        return {
            "status": "SUCCESS",
            "data": current_data,
            "steps": steps,
            "snapshots": {},
            "logs": execution_logs
        }