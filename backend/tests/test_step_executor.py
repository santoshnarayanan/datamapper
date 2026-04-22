import pytest
from app.services.step_executor import execute_step
from app.core.exceptions import StepExecutionError


def test_delete_column_success():
    data = [
        {"name": "A", "age": 10},
        {"name": "B", "age": 20},
    ]

    step = {"operation": "delete_column", "column": "age"}

    result = execute_step(step, data)

    assert result == [
        {"name": "A"},
        {"name": "B"},
    ]


def test_remove_rows_success():
    data = [
        {"name": "A"},
        {"name": "B"},
        {"name": "C"},
    ]

    step = {"operation": "remove_rows", "rows": [1]}

    result = execute_step(step, data)

    assert result == [
        {"name": "A"},
        {"name": "C"},
    ]


def test_data_error_missing_column():
    data = [{"name": "A"}]

    step = {"operation": "delete_column", "column": "age"}

    with pytest.raises(StepExecutionError) as exc:
        execute_step(step, data)

    assert exc.value.error_type == "DATA_ERROR"
    assert exc.value.retryable is False


def test_permanent_invalid_operation():
    data = [{"name": "A"}]

    step = {"operation": "invalid_op"}

    with pytest.raises(StepExecutionError) as exc:
        execute_step(step, data)

    assert exc.value.retryable is False