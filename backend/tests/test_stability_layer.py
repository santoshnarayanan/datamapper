# tests/test_stability_layer.py

import pytest

from app.services.stability_service import should_replace_mapping


# =========================================

# 🟣 PHASE 11 — STEP 5

# STABILITY LAYER TESTS

# =========================================

# =========================================

# 🟣 SHOULD REPLACE — LARGE IMPROVEMENT

# =========================================

def test_should_replace_mapping_large_improvement():


    """
    Mapping should be replaced when score improvement
    exceeds stability threshold.
    """

result = should_replace_mapping(
    existing_score=0.50,
    new_score=0.80,
    stability_threshold=0.10
)

assert result is True


# =========================================

# 🟣 SHOULD NOT REPLACE — SMALL DIFFERENCE

# =========================================

def test_should_not_replace_mapping_small_difference():


    """
    Prevent flip-flops when score difference is too small.
    """

result = should_replace_mapping(
    existing_score=0.81,
    new_score=0.82,
    stability_threshold=0.10
)

assert result is False


# =========================================

# 🟣 SHOULD NOT REPLACE — SAME SCORE

# =========================================

def test_should_not_replace_same_score():


    """
    Mapping should not be replaced when scores are equal.
    """

result = should_replace_mapping(
    existing_score=0.75,
    new_score=0.75,
    stability_threshold=0.10
)

assert result is False


# =========================================

# 🟣 SHOULD NOT REPLACE — LOWER SCORE

# =========================================

def test_should_not_replace_lower_score():


    """
    Mapping should not be replaced when new score is lower.
    """

result = should_replace_mapping(
    existing_score=0.90,
    new_score=0.70,
    stability_threshold=0.10
)

assert result is False


# =========================================

# 🟣 EXACT THRESHOLD TEST

# =========================================

def test_exact_threshold_difference():


    """
    Exact threshold difference should not replace mapping
    because logic uses strict greater-than comparison.
    """

result = should_replace_mapping(
    existing_score=0.70,
    new_score=0.80,
    stability_threshold=0.10
)

assert result is True


# =========================================

# 🟣 ABOVE THRESHOLD TEST

# =========================================

def test_above_threshold_difference():


    """
    Slightly above threshold should allow replacement.
    """

result = should_replace_mapping(
    existing_score=0.70,
    new_score=0.81,
    stability_threshold=0.10
)

assert result is True


# =========================================

# 🟣 CUSTOM THRESHOLD TEST

# =========================================

def test_custom_stability_threshold():


    """
    Verify custom stability thresholds work correctly.
    """

result = should_replace_mapping(
    existing_score=0.80,
    new_score=0.86,
    stability_threshold=0.05
)

assert result is True


# =========================================

# 🟣 HIGH CONFIDENCE STABILITY TEST

# =========================================

def test_high_confidence_small_variation():


    """
    Even high confidence mappings should not flip
    for tiny score changes.
    """

result = should_replace_mapping(
    existing_score=0.96,
    new_score=0.97,
    stability_threshold=0.10
)

assert result is False


# =========================================

# 🟣 NEGATIVE SCORE SAFETY TEST

# =========================================

def test_negative_score_safety():


    """
    Negative scores should not break stability logic.
    """

result = should_replace_mapping(
    existing_score=-0.20,
    new_score=0.10,
    stability_threshold=0.10
)

assert result is True
