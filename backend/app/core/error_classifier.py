"""
Centralized error classification logic.

Why this is critical:
--------------------
This function ensures that:
- Retry behavior is consistent across the system
- Temporal does not retry non-retryable failures
- Replay remains deterministic

Design Principle:
-----------------
We map Python exceptions → business-level error types

WARNING:
--------
Any change here affects:
- Retry behavior
- Workflow execution
- System stability

So changes must be carefully reviewed.
"""

from app.core.errors import ErrorType


def classify_error(e: Exception) -> ErrorType:
    """
        Classifies exception into retryable/non-retryable categories.

        Rules:
        ------
        Timeout / Connection → TRANSIENT → retry
        KeyError → DATA_ERROR → user issue
        ValueError → PERMANENT → invalid config
        Everything else → SYSTEM_ERROR

        NOTE:
        This mapping can be extended as system evolves.
        """

    if isinstance(e, TimeoutError):
        return ErrorType.TRANSIENT

    elif isinstance(e, ConnectionError):
        return ErrorType.TRANSIENT

    elif isinstance(e, KeyError):
        return ErrorType.DATA_ERROR

    elif isinstance(e, ValueError):
        return ErrorType.PERMANENT

    else:
        return ErrorType.SYSTEM_ERROR