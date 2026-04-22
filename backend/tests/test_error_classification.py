import pytest
from app.core.error_classifier import classify_error
from app.core.errors import ErrorType


def test_transient_timeout():
    e = TimeoutError("timeout")
    assert classify_error(e) == ErrorType.TRANSIENT


def test_transient_connection():
    e = ConnectionError("connection failed")
    assert classify_error(e) == ErrorType.TRANSIENT


def test_data_error():
    e = KeyError("missing column")
    assert classify_error(e) == ErrorType.DATA_ERROR


def test_permanent_error():
    e = ValueError("invalid config")
    assert classify_error(e) == ErrorType.PERMANENT


def test_system_error():
    e = Exception("unknown")
    assert classify_error(e) == ErrorType.SYSTEM_ERROR