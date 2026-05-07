
def generate_reason(selected_target, score, accept_count, reject_count):
    if accept_count >= 2:
        return f"Selected '{selected_target}' due to strong user acceptance history"

    if reject_count >= 3:
        return f"Other candidates were rejected frequently; '{selected_target}' chosen as best alternative"

    return f"Selected '{selected_target}' based on highest adjusted score ({round(score, 2)})"


def build_decision_trace(
    source_field,
    selected_target,
    method,
    confidence,
    rule_score,
    semantic_score,
    feedback_score,
    final_score,
    feedback_accept_count,
    feedback_reject_count,
    candidates,

    # =========================================
    # 🟣 STEP 5 — STABILITY LAYER
    # Optional stability metadata
    # =========================================
    stability_trace=None
):
    return {
        "source_field": source_field,
        "selected_target": selected_target,
        "method": method,
        "confidence": round(confidence, 4),

        "scores": {
            "rule_score": round(rule_score, 4),
            "semantic_score": round(semantic_score, 4),
            "feedback_score": round(feedback_score, 4),
            "final_score": round(final_score, 4)
        },

        "feedback_summary": {
            "accept_count": feedback_accept_count,
            "reject_count": feedback_reject_count
        },

        "candidates": [
            {
                "field": c["field"],
                "score": round(c["score"], 4)
            } for c in candidates
        ],

        # =========================================
        # 🟣 STEP 5 — STABILITY TRACE
        # Helps explain why mapping was:
        # - replaced
        # - retained
        # - blocked from changing
        # =========================================
        "stability_trace": stability_trace,

        "reason": generate_reason(
            selected_target,
            final_score,
            feedback_accept_count,
            feedback_reject_count
        )
    }


