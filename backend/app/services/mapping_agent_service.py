from app.services.mapping_suggestion_service import suggest_mappings
from app.services.vector_mapping_service import (
    semantic_search,
    store_target_columns
)

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
        if match and match["confidence"] >= 0.5:
            print(f"RULE MATCH: {src} → {match['target']} ({match['confidence']})")
            target_col = match["target"]

        else:
            print(f"AI MATCH (Pinecone): {src}")
            # 🔥 Pinecone semantic fallback
            target_col = semantic_search(src)

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