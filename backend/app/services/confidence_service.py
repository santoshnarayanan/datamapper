"""
Confidence Service

Computes calibrated confidence score based on
the decision strategy used by the mapping engine.

Strategies:
- RULE
- FEEDBACK_STRONG_ACCEPT
- FEEDBACK_STRONG_REJECT
- LLM_RAG_CONTROLLED
"""


def compute_confidence_score(
    method: str,
    rule_score: float,
    semantic_score: float,
    feedback_score: float
) -> float:
    """
    Compute confidence based on decision method.
    """

    # =========================================
    # 🔹 RULE-BASED DECISION
    # =========================================
    if method == "RULE":
        return round(rule_score, 4)

    # =========================================
    # 🔹 STRONG FEEDBACK ACCEPT
    # =========================================
    if method == "FEEDBACK_STRONG_ACCEPT":
        return round(max(feedback_score, 0.95), 4)

    # =========================================
    # 🔹 STRONG FEEDBACK REJECT
    # =========================================
    if method == "FEEDBACK_STRONG_REJECT":
        return 0.1

    # =========================================
    # 🔹 CONTROLLED AI DECISION
    # Combine multiple weak signals
    # =========================================
    w_rule = 0.3
    w_semantic = 0.5
    w_feedback = 0.2

    final_score = (
        (w_rule * rule_score) +
        (w_semantic * semantic_score) +
        (w_feedback * feedback_score)
    )

    # =========================================
    # 🔹 SAFETY CLAMP
    # =========================================
    final_score = max(0.0, min(final_score, 1.0))

    return round(final_score, 4)