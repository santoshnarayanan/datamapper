"""
Stability Service

Prevents unnecessary mapping flip-flops by enforcing
minimum score improvement thresholds before replacing
existing mappings.
"""


def should_replace_mapping(
    existing_score: float,
    new_score: float,
    stability_threshold: float = 0.10
) -> bool:
    """
    Determine whether a new mapping should replace
    an existing mapping.

    Rules:
    - Replace only if improvement exceeds threshold
    - Prevent noisy mapping oscillation
    """

    score_difference = new_score - existing_score

    return score_difference > stability_threshold