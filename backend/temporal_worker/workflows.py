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
    async def run(self, inputs: dict) -> dict:
        data = inputs["data"]
        steps = inputs["steps"]

        # 🔥 Retry Policy (Reusable)
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=5),
            maximum_attempts=3,
        )

        workflow.logger.info(f"Starting DataPrepareWorkflow with {len(steps)} steps")

        for index, step in enumerate(steps):
            action = step["action"]
            payload = step["payload"]

            workflow.logger.info(
                f"Step {index + 1}: Executing '{action}' with payload {payload}"
            )

            try:
                # ===============================
                # DELETE COLUMN
                # ===============================
                if action == "delete_column":
                    data = await workflow.execute_activity(
                        delete_column,
                        {
                            "data": data,
                            "column": payload["column"]
                        },
                        start_to_close_timeout=timedelta(seconds=10),
                        retry_policy=retry_policy,
                    )

                # ===============================
                # REMOVE ROWS
                # ===============================
                elif action == "remove_rows":
                    data = await workflow.execute_activity(
                        remove_rows,
                        {
                            "data": data,
                            "rows": payload["rows"]
                        },
                        start_to_close_timeout=timedelta(seconds=10),
                        retry_policy=retry_policy,
                    )

                # ===============================
                # MAKE HEADER
                # ===============================
                elif action == "make_header":
                    data = await workflow.execute_activity(
                        make_header,
                        {
                            "data": data
                        },
                        start_to_close_timeout=timedelta(seconds=10),
                        retry_policy=retry_policy,
                    )

                else:
                    # Unknown action
                    workflow.logger.error(f"Unknown action received: {action}")
                    raise ValueError(f"Unsupported action: {action}")

            except Exception as e:
                workflow.logger.error(
                    f"❌ Step {index + 1} FAILED ({action}) | Error: {str(e)}"
                )
                raise

        workflow.logger.info("✅ DataPrepareWorkflow completed successfully")

        return data