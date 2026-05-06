# app/services/mapping_service.py

from typing import List, Dict
from app.services.decision_trace import build_decision_trace
from app.services.confidence_service import  compute_confidence_score


# -----------------------------
# EXISTING VALIDATION (UNCHANGED)
# -----------------------------
def validate_mapping(mapping, source_columns, target_columns):
    for m in mapping:
        src = m["source"]["column"]
        tgt = m["target"]["column"]

        if src not in source_columns:
            raise ValueError(f"Invalid source column: {src}")

        if tgt not in target_columns:
            raise ValueError(f"Invalid target column: {tgt}")

    return True


# -----------------------------
# NEW: Candidate Selection Logic
# -----------------------------
def select_best_candidate(candidates: List[Dict]) -> Dict:
    """
    Select best candidate based on highest score.
    (Safe version without assuming existing logic)
    """

    if not candidates:
        return None

    best = candidates[0]

    for c in candidates:
        if c["score"] > best["score"]:
            best = c

    return best


# -----------------------------
# NEW: Main Mapping Decision Engine
# -----------------------------
def generate_mapping_decision(
    source_field,
    candidates,
    rule_score=0.0,
    semantic_score=0.0,
    feedback_score=0.0,
    accept_count=0,
    reject_count=0
):
    """
    Core decision function for selecting mapping + generating explainability
    """

    # Step 1: Select best candidate
    best_candidate = select_best_candidate(candidates)

    if not best_candidate:
        return {
            "mapping": None,
            "decision_trace": None
        }

    # Step 2: Resolve method
    method = resolve_method(
        rule_score,
        accept_count,
        reject_count
    )

    # =========================================
    # 🟣 STEP 3 — METHOD-AWARE CONFIDENCE MODEL
    # Compute confidence based on selected strategy
    # =========================================
    confidence = compute_confidence_score(
        method=method,
        rule_score=rule_score,
        semantic_score=semantic_score,
        feedback_score=feedback_score
    )

    # Step 3: Build decision trace
    decision_trace = build_decision_trace(
        source_field=source_field,
        selected_target=best_candidate["field"],
        method=method,
        confidence=confidence,

        rule_score=rule_score,
        semantic_score=semantic_score,
        feedback_score=feedback_score,

        final_score=confidence,

        feedback_accept_count=accept_count,
        feedback_reject_count=reject_count,

        candidates=candidates
    )

    # Step 4: Return result
    return {
        "mapping": {
            "source": source_field,
            "target": best_candidate["field"],
            "confidence": confidence,
            "method": method
        },
        "decision_trace": decision_trace
    }


def resolve_method(rule_score: float, accept_count: int, reject_count: int) -> str:
    """
    Determine which strategy was used to select mapping.
    """

    # Strong feedback override
    if accept_count >= 2:
        return "FEEDBACK_STRONG_ACCEPT"

    # Strong reject block (for trace clarity)
    if reject_count >= 3:
        return "FEEDBACK_STRONG_REJECT"

    # Rule-based match
    if rule_score >= 0.85:
        return "RULE"

    # Default → controlled semantic + LLM decision
    return "LLM_RAG_CONTROLLED"