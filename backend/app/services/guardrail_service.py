"""
AI Guardrail Service

Provides deterministic validation and safety checks
before AI-generated mappings are persisted.
"""


def validate_mapping_structure(mapping: dict):
    """
    Validate required mapping structure.
    """

    required_fields = [
        "source",
        "target",
        "confidence",
        "method"
    ]

    missing_fields = [
        field for field in required_fields
        if field not in mapping
    ]

    if missing_fields:
        return {
            "valid": False,
            "reason": f"Missing required fields: {missing_fields}"
        }

    return {
        "valid": True,
        "reason": "Mapping structure valid"
    }


def validate_confidence_floor(
    confidence: float,
    minimum_confidence: float = 0.50
):
    """
    Prevent extremely low-confidence mappings.
    """

    if confidence < minimum_confidence:
        return {
            "valid": False,
            "reason": (
                f"Confidence below minimum threshold "
                f"({minimum_confidence})"
            )
        }

    return {
        "valid": True,
        "reason": "Confidence validation passed"
    }


def validate_target_exists(
    target_column: str,
    available_targets: list
):
    """
    Ensure AI-selected target actually exists.
    """

    if target_column not in available_targets:
        return {
            "valid": False,
            "reason": (
                f"Target column '{target_column}' "
                f"does not exist"
            )
        }

    return {
        "valid": True,
        "reason": "Target validation passed"
    }