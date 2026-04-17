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

def apply_step(data, step):
    action = step["action"]
    payload = step["payload"]

    if action == "delete_column":
        return delete_column(data, payload["column"])

    elif action == "remove_rows":
        return remove_rows(data, payload["rows"])

    elif action == "make_header":
        return make_first_row_header(data)

    return data


def replay_steps(original_data, steps):
    data = original_data

    for step in steps:
        data = apply_step(data, step)

    return data