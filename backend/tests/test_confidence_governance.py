# tests/test_confidence_governance.py

import pytest

from app.services.governance_service import evaluate_governance


# =========================================

# 🟣 PHASE 11 — STEP 6

# CONFIDENCE GOVERNANCE TESTS

# =========================================

def test_auto_approved_governance():


    """
    High confidence mappings should be automatically approved.
    """

result = evaluate_governance(0.95)

assert result["status"] == "AUTO_APPROVED"
assert result["threshold"] == 0.90


# =========================================

# 🟣 REVIEW REQUIRED TEST

# =========================================

def test_review_required_governance():


    """
    Medium confidence mappings should require review.
    """

result = evaluate_governance(0.75)

assert result["status"] == "REVIEW_REQUIRED"
assert result["threshold"] == 0.70


# =========================================

# 🟣 LOW CONFIDENCE BLOCK TEST

# =========================================

def test_blocked_low_confidence_governance():


    """
    Low confidence mappings should be blocked.
    """

result = evaluate_governance(0.45)

assert result["status"] == "BLOCKED_LOW_CONFIDENCE"
assert result["threshold"] == 0.70


# =========================================

# 🟣 EDGE CASE — EXACT AUTO APPROVAL THRESHOLD

# =========================================

def test_exact_auto_approval_threshold():


    """
    Confidence exactly equal to auto-approval threshold
    should still pass auto-approval.
    """

result = evaluate_governance(0.90)

assert result["status"] == "AUTO_APPROVED"


# =========================================

# 🟣 EDGE CASE — EXACT REVIEW THRESHOLD

# =========================================

def test_exact_review_threshold():


    """
    Confidence exactly equal to review threshold
    should require review.
    """

result = evaluate_governance(0.70)

assert result["status"] == "REVIEW_REQUIRED"


# =========================================

# 🟣 NEGATIVE CONFIDENCE SAFETY TEST

# =========================================

def test_negative_confidence():


    """
    Negative confidence should always be blocked.
    """

result = evaluate_governance(-0.20)

assert result["status"] == "BLOCKED_LOW_CONFIDENCE"


# =========================================

# 🟣 EXTREMELY HIGH CONFIDENCE TEST

# =========================================

def test_high_confidence_upper_bound():


    """
    Confidence greater than 1.0 should still be treated
    as AUTO_APPROVED.
    """

result = evaluate_governance(1.20)

assert result["status"] == "AUTO_APPROVED"
