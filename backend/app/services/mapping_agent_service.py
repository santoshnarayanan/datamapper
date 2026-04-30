"""
PHASE 9–10: FEEDBACK-DRIVEN INTELLIGENT MAPPING ENGINE

This module implements an adaptive mapping system that evolves from
rule-based and semantic matching into a feedback-driven, self-correcting system.

----------------------------------------
PHASE 9 CAPABILITIES
----------------------------------------
- Feedback capture via API (/mapping-feedback)
- Feedback persistence (ACCEPT / REJECT)
- Historical feedback retrieval for mapping decisions

----------------------------------------
PHASE 10 CAPABILITIES
----------------------------------------
- Feedback intelligence (score boost / penalty)
- Feedback-aware candidate injection (vector layer)
- Strong feedback enforcement:
    • ACCEPT ≥ 2 → Hard override (skip AI completely)
    • REJECT ≥ 3 → Hard block (remove candidate)
- Controlled decision layer (LLM guided, NOT dominant)
- Conflict resolution handled in validation layer

----------------------------------------
SYSTEM BEHAVIOR
----------------------------------------
- Learns from user feedback over time
- Adjusts confidence dynamically
- Enforces strong user decisions deterministically
- Prevents duplicate and conflicting mappings

----------------------------------------
OUTCOME
----------------------------------------
System evolves from:
    "AI suggests mappings"
to:
    "System learns, enforces, and controls mappings"
"""


from app.services.mapping_suggestion_service import suggest_mappings
from app.services.vector_mapping_service import (
    store_target_columns, semantic_search_candidates
)
from app.services.mapping_suggestion_service import suggest_mappings

from app.core.logger import logger
import uuid

def run_mapping_agent(source_columns, target_columns, source_ws, target_ws):
    """
    BASIC RULE-BASED AGENT (Phase 7.6)

    - Uses rule-based matching only
    - No feedback, no semantic search, no learning
    """

    suggestions = suggest_mappings(source_columns, target_columns)

    mapping = [
        {
            "source": {
                "column": s["source"],
                "worksheet": source_ws
            },
            "target": {
                "column": s["target"],
                "worksheet": target_ws
            },
            "status": "MAPPED"
        }
        for s in suggestions
    ]

    return mapping


def run_hybrid_mapping_agent(
    source_columns,
    target_columns,
    source_ws,
    target_ws,
    db,
    workflow_id
):
    """
    HYBRID MAPPING AGENT (Phase 7.6 → Phase 10.4)

    Pipeline:
    1. Rule-based matching
    2. Feedback override (ACCEPT)
    3. Feedback intelligence (boost / penalty)
    4. Feedback enforcement (ACCEPT/REJECT thresholds)
    5. Semantic search (vector DB)
    6. Controlled decision (LLM guided)

    This is the core intelligent mapping engine.
    """

    request_id = str(uuid.uuid4())

    logger.info({
        "event": "agent_start",
        "source_columns": source_columns,
        "target_columns": target_columns,
        "request_id": request_id
    })

    store_target_columns(target_columns)
    suggestions = suggest_mappings(source_columns, target_columns)

    mapping = []

    from app.repositories.mapping_feedback_repo import (
        get_feedback_mapping,
        get_feedback_stats
    )

    for src in source_columns:

        confidence = 0.0
        target_col = None
        method = "NONE"

        # 🔥 CONTROL FLAG (IMPORTANT FIX)
        skip_final_append = False

        # ----------------------------------------
        # 🟢 STEP 1 — RULE-BASED MATCHING
        # ----------------------------------------
        match = next((s for s in suggestions if s["source"] == src), None)

        if match and match["confidence"] >= 0.85:
            target_col = match["target"]
            confidence = round(match["confidence"], 2)
            method = "RULE"

            logger.info({
                "event": "rule_match",
                "source": src,
                "target": target_col,
                "confidence": confidence,
                "method": method,
                "request_id": request_id
            })

        # ----------------------------------------
        # 🟣 STEP 2 — FEEDBACK OVERRIDE (ACCEPT ONLY)
        # If user explicitly ACCEPTED a mapping:
        # → System immediately uses this mapping
        # → Skips semantic search and LLM
        #
        # Important:
        # REJECT does NOT override here
        # (handled later in enforcement layer)
        #
        # Design:
        # User-confirmed mappings take highest priority
        # ----------------------------------------
        if not target_col:
            feedback = get_feedback_mapping(db, workflow_id, src)

            if feedback and feedback.final_field in target_columns:

                if feedback.action == "ACCEPT":
                    target_col = feedback.final_field
                    confidence = 0.99
                    method = "FEEDBACK"

                    logger.info({
                        "event": "feedback_accept_override",
                        "source": src,
                        "target": target_col,
                        "confidence": confidence,
                        "method": method,
                        "request_id": request_id
                    })

                else:
                    logger.info({
                        "event": "feedback_reject_no_override",
                        "source": src,
                        "rejected_target": feedback.final_field,
                        "request_id": request_id
                    })

        # ----------------------------------------
        # 🔥 STEP 3 — FEEDBACK INTELLIGENCE
        # Adjusts candidate scores based on feedback history.
        #
        # REJECT:
        # → Penalize confidence score
        #
        # ACCEPT:
        # → Boost confidence score
        #
        # Threshold-based adjustments:
        # - Count = 2 → mild adjustment
        # - Count ≥ 3 → strong adjustment
        #
        # Goal:
        # Gradual learning without abrupt behavior shifts
        # ----------------------------------------
        feedback_stats = get_feedback_stats(db, workflow_id, src)

        accepted = feedback_stats["accepted"]
        rejected = feedback_stats["rejected"]

        # ----------------------------------------
        # 🔥 STEP 3.5 — ENFORCE FEEDBACK
        # ----------------------------------------

        # 🟢 STRONG ACCEPT → HARD OVERRIDE
        for target, count in accepted.items():
            if count >= 2 and target in target_columns:

                target_col = target
                confidence = 0.95
                method = "FEEDBACK_STRONG_ACCEPT"

                logger.info({
                    "event": "feedback_strong_accept_override",
                    "source": src,
                    "target": target,
                    "count": count,
                    "request_id": request_id
                })

                # 🔥 Append ONLY ONCE
                mapping.append({
                    "source": {
                        "column": src,
                        "worksheet": source_ws
                    },
                    "target": {
                        "column": target_col,
                        "worksheet": target_ws
                    },
                    "confidence": confidence,
                    "method": method,
                    "status": "MAPPED"
                })

                logger.info({
                    "event": "mapping_finalized_strong_accept",
                    "source": src,
                    "target": target_col,
                    "confidence": confidence,
                    "method": method,
                    "request_id": request_id
                })

                # 🔥 CRITICAL FIX
                skip_final_append = True
                break

        # 🔥 Skip rest of flow completely
        if skip_final_append:
            continue

        # 🔴 STRONG REJECT → BLOCK TARGETS
        blocked_targets = set()
        for target, count in rejected.items():
            if count >= 3:
                blocked_targets.add(target)

        if blocked_targets:
            logger.info({
                "event": "feedback_strong_reject_block",
                "source": src,
                "blocked_targets": list(blocked_targets),
                "request_id": request_id
            })

        # ----------------------------------------
        # 🟡 STEP 4 — SEMANTIC SEARCH
        # ----------------------------------------
        if not target_col:
            candidates = semantic_search_candidates(src, db, workflow_id)

            if blocked_targets:
                candidates = [
                    c for c in candidates
                    if c["target"] not in blocked_targets
                ]

            if candidates:

                logger.info({
                    "event": "candidates_found",
                    "source": src,
                    "candidates": candidates,
                    "request_id": request_id
                })

                for c in candidates:
                    score = c["score"]
                    target = c["target"]

                    original_score = score

                    if target in rejected:
                        count = rejected[target]
                        if count >= 3:
                            score -= 0.2
                        elif count == 2:
                            score -= 0.1

                    if target in accepted:
                        count = accepted[target]
                        if count >= 3:
                            score += 0.2
                        elif count == 2:
                            score += 0.1

                    c["adjusted_score"] = score

                    logger.info({
                        "event": "score_adjustment",
                        "source": src,
                        "target": target,
                        "original_score": original_score,
                        "adjusted_score": score
                    })

                best_candidate = max(
                    candidates,
                    key=lambda x: x["adjusted_score"]
                )

                target_col = best_candidate["target"]
                confidence = round(best_candidate["adjusted_score"], 2)
                method = "LLM_RAG_CONTROLLED"

                logger.info({
                    "event": "controlled_decision",
                    "source": src,
                    "selected_target": target_col,
                    "confidence": confidence,
                    "method": method,
                    "request_id": request_id
                })

        # ----------------------------------------
        # 🟢 FINAL OUTPUT
        # ----------------------------------------
        if target_col:
            mapping.append({
                "source": {
                    "column": src,
                    "worksheet": source_ws
                },
                "target": {
                    "column": target_col,
                    "worksheet": target_ws
                },
                "confidence": confidence,
                "method": method,
                "status": "MAPPED"
            })

            logger.info({
                "event": "mapping_finalized",
                "source": src,
                "target": target_col,
                "confidence": confidence,
                "method": method,
                "request_id": request_id
            })

    logger.info({
        "event": "agent_complete",
        "total_mappings": len(mapping),
        "request_id": request_id
    })

    return mapping