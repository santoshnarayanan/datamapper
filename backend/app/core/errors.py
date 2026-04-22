"""
Error classification enum used across the DataPrepare execution engine.

Why this exists:
----------------
Not all failures should be treated the same.

We classify errors to:
1. Decide retry behavior (Temporal integration)
2. Maintain deterministic replay
3. Avoid corrupting step history

IMPORTANT GUARANTEES:
---------------------
- TRANSIENT → Safe to retry (network, DB issues)
- DATA_ERROR → User/data issue → NEVER retry
- PERMANENT → Invalid configuration → NEVER retry
- SYSTEM_ERROR → Unexpected → fail fast

This classification directly impacts:
- Retry policy
- Execution logs
- Replay consistency
"""


from enum import Enum


class ErrorType(str, Enum):
    TRANSIENT = "TRANSIENT"      # retryable (network/db issues)
    PERMANENT = "PERMANENT"      # invalid config
    DATA_ERROR = "DATA_ERROR"    # user data issue
    SYSTEM_ERROR = "SYSTEM_ERROR"  # unknown/internal error