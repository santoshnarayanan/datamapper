"""
Temporal activity for step execution.

Why this layer exists:
----------------------
Temporal handles retries, but:
- It needs to know WHICH errors are retryable
- It should NOT retry data/config errors

Key Behavior:
-------------
- Retryable errors → raise Exception → Temporal retries
- Non-retryable → ApplicationFailure(non_retryable=True)

This ensures:
-------------
✔ Controlled retries
✔ No infinite retry loops
✔ Deterministic failure handling
"""

from temporalio import activity
from temporalio.exceptions import ApplicationError

from app.services.step_executor import execute_step
from app.core.exceptions import StepExecutionError


@activity.defn
async def apply_step_activity(step: dict, data: dict):
    try:
        return execute_step(step, data)

    except StepExecutionError as e:

        # 🔥 ALWAYS use ApplicationError for proper propagation
        raise ApplicationError(
            message=e.message,
            non_retryable=not e.retryable
        )