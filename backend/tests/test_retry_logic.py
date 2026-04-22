"""
Tests retry behavior WITHOUT Temporal.

Why:
----
We simulate retry logic at unit level to validate:
- Transient failures retry
- Retry stops after success

NOTE:
-----
Temporal integration tests will be added later.
"""

import pytest
import app.services.step_executor as step_executor


class TransientFailSimulator:
    def __init__(self):
        self.attempts = 0

    def run(self, step, data):
        self.attempts += 1

        if self.attempts < 3:
            raise TimeoutError("temporary failure")

        return [{"name": "Recovered"}]


def test_transient_retry_simulation(monkeypatch):
    simulator = TransientFailSimulator()

    def mock_execute(step, data):
        return simulator.run(step, data)

    # 🔥 PATCH CORRECT MODULE REFERENCE
    monkeypatch.setattr(
        step_executor,
        "execute_step",
        mock_execute
    )

    step = {"operation": "delete_column", "column": "age"}
    data = [{"name": "A", "age": 10}]

    retries = 0
    max_retries = 3

    while retries < max_retries:
        try:
            result = step_executor.execute_step(step, data)
            break
        except Exception:
            retries += 1

    assert retries == 2
    assert result == [{"name": "Recovered"}]