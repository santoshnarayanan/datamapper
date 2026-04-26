from app.services.mapping_suggestion_service import suggest_mappings
from app.services.vector_mapping_service import (
    store_target_columns, semantic_search_candidates
)
from app.services.llm_service import choose_best_mapping
from app.services.vector_mapping_service import get_domain_knowledge

def run_mapping_agent(source_columns, target_columns, source_ws, target_ws):

    from app.services.mapping_suggestion_service import suggest_mappings

    print("inside run_mapping_agent")
    print("SOURCE:", source_columns)
    print("TARGET:", target_columns)

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
    print("inside run_hybrid_mapping_agent")
    print("SOURCE:", source_columns)
    print("TARGET:", target_columns)

    # 🔥 Store target columns in Pinecone
    store_target_columns(target_columns)

    suggestions = suggest_mappings(source_columns, target_columns)

    mapping = []

    for src in source_columns:

        match = next((s for s in suggestions if s["source"] == src), None)

        # 🟢 Rule-based high confidence
        if match and match["confidence"] >= 0.6:
            print(f"RULE MATCH: {src} → {match['target']} ({match['confidence']})")
            target_col = match["target"]
        else:
            # 🔥 Get candidates
            candidates = semantic_search_candidates(src)

            if candidates:
                print("CANDIDATES:", candidates)

                # 🔥 NEW: get knowledge
                knowledge = get_domain_knowledge(src)
                print("KNOWLEDGE:", knowledge)

                # 🔥 FIX: pass knowledge to LLM
                target_col = choose_best_mapping(src, candidates, knowledge)

                print("LLM SELECTED:", target_col)
            else:
                target_col = None

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
                "status": "MAPPED"
            })

    return mapping