import pytest
from app.services.step_executor import execute_step
from app.core.exceptions import StepExecutionError


def test_mixed_execution_flow():
    data = [
        {"name": "A", "age": 10},
        {"name": "B", "age": 20},
    ]

    steps = [
        {"operation": "delete_column", "column": "age"},   # success
        {"operation": "remove_rows", "rows": [0]},         # success
        {"operation": "delete_column", "column": "age"},   # FAIL
    ]

    current_data = data

    success_count = 0

    for step in steps:
        try:
            current_data = execute_step(step, current_data)
            success_count += 1
        except StepExecutionError as e:
            assert e.retryable is False
            break

    assert success_count == 2