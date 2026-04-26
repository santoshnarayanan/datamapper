from app.services.mapping_suggestion_service import suggest_mappings


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