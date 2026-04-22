"""
Custom exception used during step execution.

Why we need this:
-----------------
Standard exceptions (KeyError, ValueError, etc.)
do not carry retry semantics.

This wrapper ensures:
- Every failure has a classification
- Retry decision is explicit
- Logs are structured

Fields:
-------
message → human-readable error
error_type → classification (from ErrorType)
retryable → controls Temporal retry behavior
"""

class StepExecutionError(Exception):
    def __init__(self, message: str, error_type: str, retryable: bool):
        self.message = message
        self.error_type = error_type
        self.retryable = retryable
        super().__init__(message)