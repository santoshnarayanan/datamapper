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

    # 🔥 NORMALIZATION FUNCTION (NEW)
    def normalize(val):
        return val.strip().lower()

    # 🔥 PRE-COMPUTE NORMALIZED LISTS (NEW)
    normalized_source_columns = [normalize(c) for c in source_columns]
    normalized_target_columns = [normalize(c) for c in target_columns]

    seen_sources = set()
    seen_targets = set()

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
        # 🔥 Column validation (FIXED)
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
        # 🔹 Duplicate validation
        # =========================
        src_key = (src["worksheet"], src_col_normalized)
        tgt_key = tgt_col_normalized

        if src_key in seen_sources:
            raise HTTPException(
                status_code=400,
                detail=f"Duplicate source mapping: {src['column']}"
            )

        if tgt_key in seen_targets:
            raise HTTPException(
                status_code=400,
                detail=f"Duplicate target mapping: {tgt['column']}"
            )

        seen_sources.add(src_key)
        seen_targets.add(tgt_key)