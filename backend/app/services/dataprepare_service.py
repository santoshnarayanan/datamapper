def delete_column(data, column_name):
    columns = data["columns"]
    rows = data["rows"]

    if column_name not in columns:
        return data

    columns.remove(column_name)

    for row in rows:
        row.pop(column_name, None)

    return {"columns": columns, "rows": rows}


def remove_rows(data, row_indices):
    rows = data["rows"]

    new_rows = [
        row for i, row in enumerate(rows)
        if i not in row_indices
    ]

    return {
        "columns": data["columns"],
        "rows": new_rows
    }


def make_first_row_header(data):
    rows = data["rows"]

    if not rows:
        return data

    new_columns = list(rows[0].values())
    new_rows = rows[1:]

    return {
        "columns": new_columns,
        "rows": new_rows
    }