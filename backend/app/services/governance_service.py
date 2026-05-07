"""
Governance Service

Controls whether AI-generated mappings are:
- automatically approved
- flagged for review
- blocked due to low confidence
"""


def evaluate_governance(confidence: float):
    """
    Evaluate mapping governance policy based on confidence.
    """

    # =========================================
    # 🟣 HIGH CONFIDENCE
    # Safe for automatic approval
    # =========================================
    if confidence >= 0.90:
        return {
            "status": "AUTO_APPROVED",
            "threshold": 0.90,
            "reason": "Confidence exceeds auto-approval threshold"
        }

    # =========================================
    # 🟣 MEDIUM CONFIDENCE
    # Human review recommended
    # =========================================
    if confidence >= 0.70:
        return {
            "status": "REVIEW_REQUIRED",
            "threshold": 0.70,
            "reason": "Confidence requires human validation"
        }

    # =========================================
    # 🟣 LOW CONFIDENCE
    # Block automatic mapping
    # =========================================
    return {
        "status": "BLOCKED_LOW_CONFIDENCE",
        "threshold": 0.70,
        "reason": "Confidence below minimum governance threshold"
    }