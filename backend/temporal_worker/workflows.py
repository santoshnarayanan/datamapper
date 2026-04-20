from temporalio import workflow
from temporalio.common import RetryPolicy
from datetime import timedelta

with workflow.unsafe.imports_passed_through():
    from temporal_worker.activities import (
        say_hello, delete_column, remove_rows, make_header
    )


# ===============================
# HELLO WORKFLOW (UNCHANGED)
# ===============================
@workflow.defn
class HelloWorkflow:

    @workflow.run
    async def run(self, name: str) -> str:
        result = await workflow.execute_activity(
            say_hello,
            name,
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(
                maximum_attempts=1
            ),
        )
        return result


# ===============================
# DATAPREPARE WORKFLOW (ENHANCED)
# ===============================
@workflow.defn
class DataPrepareWorkflow:

    @workflow.run
    async def run(self, input_data: dict) -> dict:
        data = input_data["data"]
        steps = input_data["steps"]

        execution_log = []

        for idx, step in enumerate(steps, start=1):
            action = step["action"]
            payload = step["payload"]

            try:
                # 🔥 execute activity
                data = await workflow.execute_activity(
                    action,
                    {
                        "data": data,
                        **payload
                    },
                    start_to_close_timeout=timedelta(seconds=10),

                    # 🔥 ADD THIS
                    retry_policy=RetryPolicy(
                        maximum_attempts=1  # or 2 if you want minimal retry
                    )
                )

                # ✅ success log
                execution_log.append({
                    "step": idx,
                    "action": action,
                    "status": "success"
                })

            except Exception as e:
                # ❌ failure log
                execution_log.append({
                    "step": idx,
                    "action": action,
                    "status": "failed",
                    "error": str(e)
                })

                # 🔥 stop execution on failure
                return {
                    "status": "failed",
                    "error": str(e),
                    "failed_step": idx,
                    "execution_log": execution_log
                }

        # ✅ all success
        return {
            "status": "success",
            "data": data,
            "execution_log": execution_log
        }