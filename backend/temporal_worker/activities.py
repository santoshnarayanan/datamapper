from temporalio import activity


@activity.defn
async def say_hello(name: str) -> str:
    return f"Hello, {name}"


# ✅ FIXED
@activity.defn
async def delete_column(input_data: dict) -> dict:
    data = input_data["data"]
    column = input_data["column"]

    # 🔥 Validation (IMPORTANT)
    if column not in data["columns"]:
        raise ValueError(f"Column '{column}' not found")

    # remove column from columns list
    data["columns"] = [c for c in data["columns"] if c != column]

    # remove column from each row
    for row in data["rows"]:
        row.pop(column, None)

    return data


# ✅ FIXED
@activity.defn
async def remove_rows(input_data: dict) -> dict:
    data = input_data["data"]
    rows = input_data["rows"]

    data["rows"] = [
        row for idx, row in enumerate(data["rows"])
        if idx not in rows
    ]

    return data


# ✅ FIXED
@activity.defn
async def make_header(input_data: dict) -> dict:
    data = input_data["data"]

    if not data["rows"]:
        return data

    headers = list(data["rows"][0].values())
    new_rows = data["rows"][1:]

    data["columns"] = headers
    data["rows"] = new_rows

    return data