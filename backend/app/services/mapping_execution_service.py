def execute_mapping(source_rows, mapping):
    """
    Applies column-level mapping to source rows.

    Args:
        source_rows (list): List of dictionaries (input data)
        mapping (list): Mapping definitions

    Returns:
        list: Transformed rows (target format)
    """

    if not source_rows:
        return []

    if not mapping:
        return []

    # Build mapping lookup
    mapping_lookup = {
        m["target"]["column"]: m["source"]["column"]
        for m in mapping
    }

    result = []

    for row in source_rows:
        new_row = {}

        for target_col, source_col in mapping_lookup.items():
            new_row[target_col] = row.get(source_col)

        result.append(new_row)

    return result