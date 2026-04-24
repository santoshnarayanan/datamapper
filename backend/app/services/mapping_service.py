def validate_mapping(mapping, source_columns, target_columns):
    for m in mapping:
        src = m["source"]["column"]
        tgt = m["target"]["column"]

        if src not in source_columns:
            raise ValueError(f"Invalid source column: {src}")

        if tgt not in target_columns:
            raise ValueError(f"Invalid target column: {tgt}")

    return True