from datetime import datetime
from math import exp


def compute_recency_weight(created_at, decay_rate=0.05):
    """
    Compute time-decayed weight for feedback.

    More recent feedback has stronger influence.
    Older feedback gradually loses impact.
    """

    now = datetime.utcnow()

    age_days = (now - created_at).days

    weight = exp(-decay_rate * age_days)

    return round(weight, 4)


def compute_feedback_score(feedback_entries):
    """
    Compute weighted feedback score using:
    - action type
    - recency decay
    """

    score = 0.0

    for feedback in feedback_entries:

        recency_weight = compute_recency_weight(
            feedback.created_at
        )

        # =========================================
        # ACCEPT increases confidence
        # =========================================
        if feedback.action == "ACCEPT":
            score += (1.0 * recency_weight)

        # =========================================
        # REJECT decreases confidence
        # =========================================
        elif feedback.action == "REJECT":
            score -= (1.0 * recency_weight)

    return round(score, 4)