from app.services.mapping_suggestion_service import suggest_mappings
from app.services.vector_mapping_service import (
    store_target_columns, semantic_search_candidates
)
from app.services.llm_service import choose_best_mapping
from app.services.vector_mapping_service import get_domain_knowledge

from app.core.logger import logger
import uuid

def run_mapping_agent(source_columns, target_columns, source_ws, target_ws):

    from app.services.mapping_suggestion_service import suggest_mappings

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


# Hybrid mapping logic:
# 1. Try rule-based match (fast, deterministic)
# 2. If confidence is low → fallback to Pinecone semantic search
def run_hybrid_mapping_agent(
    source_columns,
    target_columns,
    source_ws,
    target_ws
):
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

    for src in source_columns:

        confidence = 0.0
        target_col = None
        method = "NONE"

        match = next((s for s in suggestions if s["source"] == src), None)

        # 🟢 RULE
        if match and match["confidence"] >= 0.6:
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

        else:
            candidates = semantic_search_candidates(src)

            if candidates:
                logger.info({
                    "event": "candidates_found",
                    "source": src,
                    "candidates": candidates,
                    "request_id": request_id
                })

                best_candidate = max(candidates, key=lambda x: x["score"])
                confidence = round(best_candidate["score"], 2)

                knowledge = get_domain_knowledge(src)

                logger.info({
                    "event": "rag_knowledge",
                    "source": src,
                    "knowledge": knowledge,
                    "request_id": request_id
                })

                target_col = choose_best_mapping(src, candidates, knowledge)
                method = "LLM_RAG"

                logger.info({
                    "event": "llm_decision",
                    "source": src,
                    "selected_target": target_col,
                    "confidence": confidence,
                    "method": method,
                    "request_id": request_id
                })

            else:
                logger.info({
                    "event": "no_candidates",
                    "source": src,
                    "request_id": request_id
                })

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