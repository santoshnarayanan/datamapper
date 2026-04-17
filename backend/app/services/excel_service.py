import pandas as pd

def parse_excel(file):
    df = pd.read_excel(file, engine='openpyxl')

    df = df.fillna("")

    return {
        "columns": df.columns.tolist(),
        "rows": df.to_dict(orient='records')
    }