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

from app.core.error_classifier import classify_error
from app.core.exceptions import StepExecutionError
from app.core.errors import ErrorType


def execute_step(step: dict, data: list) -> list:
    """
       Executes a single transformation step.

       Parameters:
       -----------
       step → transformation instruction
       data → current dataset state

       Returns:
       --------
       Updated dataset

       Raises:
       -------
       StepExecutionError (ALWAYS wrapped)

       IMPORTANT:
       ----------
       - No mutation of input data
       - All failures must be classified
       """

    try:
        operation = step.get("operation")

        if operation == "delete_column":
            col = step["column"]

            # Validate column existence BEFORE execution
            # This prevents silent failures and ensures deterministic replay

            # 🔥 ADD THIS CHECK
            if col not in data[0]:
                raise KeyError(f"Column '{col}' not found")

            return [
                {k: v for k, v in row.items() if k != col}
                for row in data
            ]

        elif operation == "remove_rows":
            index_list = step["rows"]
            return [
                row for idx, row in enumerate(data)
                if idx not in index_list
            ]

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