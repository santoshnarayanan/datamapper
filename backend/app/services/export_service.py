import pandas as pd
from io import BytesIO


def generate_excel(data: list):
    """
    Convert data to Excel file in memory
    """
    df = pd.DataFrame(data)

    output = BytesIO()
    df.to_excel(output, index=False)

    output.seek(0)
    return output


def generate_csv(data: list):
    """
    Convert data to CSV file in memory
    """
    df = pd.DataFrame(data)

    output = BytesIO()
    df.to_csv(output, index=False)

    output.seek(0)
    return output