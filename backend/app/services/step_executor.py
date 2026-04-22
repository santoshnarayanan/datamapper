"""
Step execution engine for DataPrepare.

This module is responsible for:
- Applying transformation steps
- Validating input data
- Raising classified errors

CRITICAL DESIGN RULES:
----------------------
1. NO side effects (pure function)
2. Deterministic execution
3. Fail fast on invalid data
4. NEVER silently ignore errors

Why?
----
Because this function is used in:
- Temporal workflows
- Replay engine
- Undo functionality

Any non-determinism here will break the entire system.
"""

from typing import Dict
from app.core.error_classifier import classify_error
from app.core.exceptions import StepExecutionError
from app.core.errors import ErrorType


def execute_step(step: dict, data: dict) -> dict:

    try:
        operation = step.get("operation")

        if operation == "delete_column":
            col = step["column"]

            if col not in data["columns"]:
                raise KeyError(f"Column '{col}' not found")

            return {
                "columns": [c for c in data["columns"] if c != col],
                "rows": [
                    {k: v for k, v in row.items() if k != col}
                    for row in data["rows"]
                ]
            }

        elif operation == "remove_rows":
            index_list = step["rows"]

            return {
                "columns": data["columns"],
                "rows": [
                    row for idx, row in enumerate(data["rows"])
                    if idx not in index_list
                ]
            }

        else:
            raise ValueError(f"Unsupported operation: {operation}")

    except Exception as e:
        error_type = classify_error(e)
        retryable = error_type == ErrorType.TRANSIENT

        raise StepExecutionError(
            message=str(e),
            error_type=error_type,
            retryable=retryable
        )