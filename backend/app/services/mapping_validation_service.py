from fastapi import HTTPException


def validate_mapping_request(
    mapping_list,
    source_columns,
    target_columns,
    source_ws,
    target_ws
):
    if not mapping_list:
        raise HTTPException(
            status_code=400,
            detail="Mapping list cannot be empty"
        )

    # 🔥 NORMALIZATION FUNCTION
    def normalize(val):
        return val.strip().lower()

    # 🔥 PRE-COMPUTE NORMALIZED LISTS
    normalized_source_columns = [normalize(c) for c in source_columns]
    normalized_target_columns = [normalize(c) for c in target_columns]

    seen_sources = set()

    # 🔥 NEW: Track best mapping per target
    best_target_map = {}

    for m in mapping_list:

        # =========================
        # 🔹 Structure validation
        # =========================
        if "source" not in m or "target" not in m:
            raise HTTPException(
                status_code=400,
                detail="Invalid mapping structure"
            )

        src = m["source"]
        tgt = m["target"]

        # =========================
        # 🔹 Worksheet validation
        # =========================
        if src["worksheet"] != source_ws:
            raise HTTPException(
                status_code=400,
                detail=f"Source worksheet mismatch: {src['worksheet']}"
            )

        if tgt["worksheet"] != target_ws:
            raise HTTPException(
                status_code=400,
                detail=f"Target worksheet mismatch: {tgt['worksheet']}"
            )

        # =========================
        # 🔥 Column validation
        # =========================
        src_col_normalized = normalize(src["column"])
        tgt_col_normalized = normalize(tgt["column"])

        if src_col_normalized not in normalized_source_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid source column: {src['column']}"
            )

        if tgt_col_normalized not in normalized_target_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid target column: {tgt['column']}"
            )

        # =========================
        # 🔹 Duplicate source validation
        # =========================
        src_key = (src["worksheet"], src_col_normalized)

        if src_key in seen_sources:
            raise HTTPException(
                status_code=400,
                detail=f"Duplicate source mapping: {src['column']}"
            )

        seen_sources.add(src_key)

        # =========================
        # 🔥 NEW: Duplicate target resolution (BEST LOGIC)
        # If multiple sources map to same target:
        # → Compare confidence scores
        # → Retain highest confidence mapping
        # → Replace weaker mapping
        #
        # Why:
        # Avoid conflicts while preserving best mapping quality
        #
        # Note:
        # This replaces earlier strict validation which blocked duplicates
        # =========================
        new_conf = m.get("confidence", 0)

        if tgt_col_normalized in best_target_map:
            existing_mapping = best_target_map[tgt_col_normalized]
            existing_conf = existing_mapping.get("confidence", 0)

            # 🔥 Replace ONLY if new mapping is stronger
            if new_conf > existing_conf:
                best_target_map[tgt_col_normalized] = m

        else:
            best_target_map[tgt_col_normalized] = m

    # 🔥 IMPORTANT: Update original list with resolved mappings
    mapping_list.clear()
    mapping_list.extend(best_target_map.values())